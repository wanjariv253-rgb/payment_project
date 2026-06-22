import hashlib
import uuid
import requests
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import redirect
from Payment.serializers.payment_payu_serializer import TransactionInitiateSerializer
from Payment.model.payment_payu import Transaction  
from django.conf import settings

# PayU Credentials
PAYU_KEY = settings.PAYU_KEY
PAYU_SALT = settings.PAYU_SALT
PAYU_URL = settings.PAYU_URL

# ========================================================
# 1. GENERATE PAYMENT LINK (Pure JSON - NO HTML AT ALL)
# ========================================================
@api_view(['POST'])
def generate_payment_link(request):
    try:
        serializer = TransactionInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Clean Data Extraction
        validated_data = serializer.validated_data
        loan_ac_no = validated_data['loan_ac_no']
        city = validated_data['city']
        amount = validated_data['amount']
        customer_name = validated_data['customer_name']
        email = validated_data['email']
        phone = validated_data['phone']
        productinfo = validated_data['productinfo']

        # Unique Txn ID aur DB Insertion
        txnid = f"Txn{uuid.uuid4().hex[:10].upper()}"
        serializer.save(txnid=txnid, status='PENDING')
        
        # Callback Endpoints
        surl = settings.PAYU_SUCCESS_URL
        furl = settings.PAYU_FAILURE_URL


        # Cryptographic Hash
        hash_string = f"{PAYU_KEY}|{txnid}|{amount}|{productinfo}|{customer_name}|{email}|||||||||||{PAYU_SALT}"
        generated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

        # Payload Structure
        payload = {
            "key": PAYU_KEY,
            "txnid": txnid,
            "amount": str(amount),
            "productinfo": productinfo,
            "firstname": customer_name,
            "email": email,
            "phone": phone,
            "surl": surl,
            "furl": furl,
            "hash": generated_hash
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # Backend-to-Server Session Handshake (Bina redirects allow kiye)
        payu_response = requests.post(PAYU_URL, data=payload, headers=headers, allow_redirects=False)

        # 302 Found response se dynamic Location Header URL nikalna
        if payu_response.status_code in [301, 302, 303]:
            redirect_url = payu_response.headers.get('Location')
        else:
            redirect_url = payu_response.url

        # Pure Clean JSON Response returning to Postman/Client
        return Response({
            "status": "success",
            "message": "Payment link generated successfully.",
            "txnid": txnid,
            "payment_url": redirect_url
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([FormParser, MultiPartParser])
def payu_payment_callback(request):
    try:
        txnid = request.data.get('txnid')
        payu_hash = request.data.get('hash')
        status_val = request.data.get('status') 
        amount = request.data.get('amount')
        customer_name = request.data.get('firstname')
        email = request.data.get('email')
        productinfo = request.data.get('productinfo')
        key = request.data.get('key')

        if not txnid or not status_val:
            return Response({"error": "Data incomplete hai!"}, status=status.HTTP_400_BAD_REQUEST)

        reverse_hash_string = f"{PAYU_SALT}|{status_val}|||||||||||{email}|{customer_name}|{productinfo}|{amount}|{txnid}|{key}"
        calculated_hash = hashlib.sha512(reverse_hash_string.encode('utf-8')).hexdigest().lower()

        if calculated_hash != payu_hash:
            return Response({"error": "Hash Mismatch! Security block."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction_obj = Transaction.objects.get(txnid=txnid)
        except Transaction.objects.DoesNotExist:
            return Response({"error": "Transaction not found in Database"}, status=status.HTTP_404_NOT_FOUND)
        
        amount = transaction_obj.amount
        
        if status_val and status_val.lower() == "success":
            transaction_obj.status = 'SUCCESS'
            transaction_obj.save()

            return redirect(
                f"{settings.FRONTEND_URL}/payment-success?"
                f"txnid={txnid}&amount={amount}"
            )

        else:
            transaction_obj.status = 'FAILED'
            transaction_obj.save()

            return redirect(
                f"{settings.FRONTEND_URL}/payment-failure?"
                f"txnid={txnid}&amount={amount}"
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    