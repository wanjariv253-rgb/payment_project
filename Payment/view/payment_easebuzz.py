import hashlib
import uuid
import requests
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from Payment.model.payment_easebuzz import Transaction_easebuzz  
from Payment.serializers.payment_easebuzz_serializers import TransactionEasebuzzSerializer
from django.shortcuts import redirect
# Exact Easebuzz Sandbox Credentials
MERCHANT_KEY = settings.EASEBUZZ_MERCHANT_KEY
SALT = settings.EASEBUZZ_SALT

BASE_URL = (
    settings.EASEBUZZ_PROD_URL
    if settings.EASEBUZZ_ENV.lower() == "prod"
    else settings.EASEBUZZ_TEST_URL
)

@api_view(['POST'])
def generate_easebuzz_link(request):
    try:
        serializer = TransactionEasebuzzSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Clean Data Extraction
        validated_data = serializer.validated_data
        loan_ac_no = str(validated_data['loan_ac_no']).strip()
        city = str(validated_data['city']).strip()
        amount = f"{float(validated_data['amount']):.2f}"
        customer_name = str(validated_data['customer_name']).strip()
        email = str(validated_data['email']).strip()
        phone = str(validated_data['phone']).strip()
        productinfo = str(validated_data['productinfo']).strip()

        # Unique Txn ID aur DB Entry
        txnid = f"EB{uuid.uuid4().hex[:10].upper()}"
        serializer.save(txnid=txnid, status='PENDING')
        
        # Unified callback endpoint
        callback_url = settings.EASEBUZZ_CALLBACK_URL

        # Easebuzz demands all 10 UDF slots to be present for correct pipe counting
        udf1 = udf2 = udf3 = udf4 = udf5 = udf6 = udf7 = udf8 = udf9 = udf10 = ""

        # 2. Strict Hash String Construction (Pure 10 UDF Slots Pattern)
        # Formula: key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10|salt
        hash_string = f"{MERCHANT_KEY}|{txnid}|{amount}|{productinfo}|{customer_name}|{email}|{udf1}|{udf2}|{udf3}|{udf4}|{udf5}|{udf6}|{udf7}|{udf8}|{udf9}|{udf10}|{SALT}"
        generated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

        # 3. Form Payload (Form-Urlencoded mapping matches exactly)
        payload = {
            "key": str(MERCHANT_KEY).strip(),
            "txnid": str(txnid),
            "amount": str(amount),
            "productinfo": str(productinfo),
            "firstname": str(customer_name),
            "email": str(email),
            "phone": str(phone),
            "surl": str(callback_url),
            "furl": str(callback_url),
            "hash": str(generated_hash),
            "udf1": "", "udf2": "", "udf3": "", "udf4": "", "udf5": "",
            "udf6": "", "udf7": "", "udf8": "", "udf9": "", "udf10": ""
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        initiate_url = f"{BASE_URL}/payment/initiateLink"
        
        # Server-to-server POST Request
        eb_response = requests.post(initiate_url, data=payload, headers=headers)
        
        try:
            response_json = eb_response.json()
        except ValueError:
            return Response({
                "error": "Gateway returned bad/raw response format", 
                "raw_body": eb_response.text
            }, status=status.HTTP_502_BAD_GATEWAY)

        # 4. Token handling
        if response_json.get("status") == 1:
            access_key = response_json.get("data")
            checkout_url = f"{BASE_URL}/pay/{access_key}"
            
            return Response({
                "status": "success",
                "txnid": txnid,
                "payment_url": checkout_url
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "error": "Easebuzz token initiation failed", 
                "details": response_json
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================================
# 2. UNIFIED CALLBACK FOR EASEBUZZ (Success & Failure)
# ========================================================
@api_view(['POST'])
@parser_classes([FormParser, MultiPartParser])
def easebuzz_payment_callback(request):

    try:
        txnid = request.data.get('txnid')
        easebuzz_hash = request.data.get('hash')
        status_val = request.data.get('status')  
        amount = request.data.get('amount')
        customer_name = request.data.get('firstname')
        email = request.data.get('email')
        productinfo = request.data.get('productinfo')
        key = request.data.get('key')
        
        udf1 = request.data.get('udf1', '')
        udf2 = request.data.get('udf2', '')
        udf3 = request.data.get('udf3', '')
        udf4 = request.data.get('udf4', '')
        udf5 = request.data.get('udf5', '')
        udf6 = request.data.get('udf6', '')
        udf7 = request.data.get('udf7', '')
        udf8 = request.data.get('udf8', '')
        udf9 = request.data.get('udf9', '')
        udf10 = request.data.get('udf10', '')

        if not txnid or not status_val:
            return Response({"error": "Data is Incomplete"}, status=status.HTTP_400_BAD_REQUEST)

        # Reverse Hash Formula: salt|status|udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key
        reverse_hash_string = (
        f"{SALT}|{status_val}|"
        f"{udf10}|{udf9}|{udf8}|{udf7}|{udf6}|"
        f"{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|"
        f"{email}|{customer_name}|{productinfo}|{amount}|{txnid}|{key}"
        )
        calculated_hash = hashlib.sha512(reverse_hash_string.encode('utf-8')).hexdigest().lower()        
        if calculated_hash != easebuzz_hash:
            return Response({"error": "Hash Mismatch! Security Alert."}, status=status.HTTP_400_BAD_REQUEST)

        # Database transaction retrieval
        try:
            transaction_obj = Transaction_easebuzz.objects.get(txnid=txnid)
        except Transaction_easebuzz.objects.DoesNotExist:
            return Response({"error": "Transaction ID is not in Database"}, status=status.HTTP_404_NOT_FOUND)
        amount = transaction_obj.amount
        
        # Dynamic mapping for status
        if status_val and status_val.lower() == "success":
            transaction_obj.status = 'SUCCESS'
            transaction_obj.save()

            return redirect(
                f"{settings.FRONTEND_URL}/payment-success?"
                f"txnid={txnid}"
                f"&amount={amount}"
                f"&gateway=easebuzz"
            )

        else:
            transaction_obj.status = 'FAILED'
            transaction_obj.save()

            return redirect(
                f"{settings.FRONTEND_URL}/payment-failure?"
                f"txnid={txnid}"
                f"&amount={amount}"
                f"&gateway=easebuzz"
            )

        # transaction_obj.save()

        # return Response({
        #     "status": api_status,
        #     "message": f"Easebuzz Transaction {txnid} marked as {db_status} in DB."
        # }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    