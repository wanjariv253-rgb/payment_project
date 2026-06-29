import hashlib
import uuid
import requests
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from django.conf import settings
import datetime
# Models, Serializers aur Services Imports
from Payment.model.payment_easebuzz import Transaction_easebuzz  
from Payment.serializers.payment_easebuzz_serializers import TransactionEasebuzzSerializer
from Payment.model.get_payment import GetPayment
from Payment.constants import PaymentLogTypes, DEFAULT_PRODUCT_INFO
from Payment.services.all_cloud_service import AllCloudService

# Exact Easebuzz Sandbox Credentials
MERCHANT_KEY = settings.EASEBUZZ_MERCHANT_KEY
SALT = settings.EASEBUZZ_SALT

BASE_URL = (
    settings.EASEBUZZ_PROD_URL
    if settings.EASEBUZZ_ENV.lower() == "prod"
    else settings.EASEBUZZ_TEST_URL
)

# ========================================================
# 1. GENERATE PAYMENT LINK FOR EASEBUZZ
# ========================================================
@api_view(['POST'])
def generate_easebuzz_link(request):
    try:
        serializer = TransactionEasebuzzSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Clean Data Extraction
        validated_data = serializer.validated_data
        amount = f"{float(validated_data['amount']):.2f}"

        # 🔄 FRONTEND SE PARENT LOG ID NIKALI
        parent_id = request.data.get('parent_log_id')

        # 🤝 Product info ko constants.py ke default fallback se set kiya agar frontend se na aaye
        product_info_val = validated_data.get('productinfo') or DEFAULT_PRODUCT_INFO

        # 🎯 CUSTOM PAYLOAD STRUCTURE FOR LOGS (Jaise PayU me banaya tha)
        indian_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        init_date = indian_now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

        custom_log_payload = {
            "ChartOfAccountId": int(settings.ALLCLOUD_CHART_OF_ACCOUNT_ID),
            "AgreementNumber": validated_data.get('loan_ac_no'),  
            "ReceivedDate": init_date,  # 🔥 Shuruat me hi Indian Init Time chala gaya
            "Amount": float(amount),
            "LoanReceiptMode": 2,                                 
            "PolicyPaymentTypeId": settings.ALLCLOUD_POLICY_PAYMENT_TYPE_ID
        }

        # 📑 STEP 1: Central log me custom format ke sath record banaya
        db_log = GetPayment.objects.create(
            parent_id=parent_id,                     
            type=PaymentLogTypes.POST_LOAN_DETAILS,  
            request_payload=custom_log_payload,            
            response_payload={"info": "Initiating Easebuzz handshake..."},
            status_code=201
        )

        # Unique Txn ID
        txnid = f"EB{uuid.uuid4().hex[:10].upper()}"
        
        # 📑 STEP 2: Save Data into payment_easebuzz with Foreign Key & Fallback Product Info
        serializer.save(
            txnid=txnid, 
            status='PENDING',
            payment_log=db_log,
            productinfo=product_info_val
        )
        
        # Unified callback endpoint
        callback_url = settings.EASEBUZZ_CALLBACK_URL

        # Easebuzz demands all 10 UDF slots to be present for correct pipe counting
        udf1 = udf2 = udf3 = udf4 = udf5 = udf6 = udf7 = udf8 = udf9 = udf10 = ""

        # Cryptographic Hash String Construction using product_info_val constant
        hash_string = f"{MERCHANT_KEY}|{txnid}|{amount}|{product_info_val}|{validated_data['customer_name']}|{validated_data['email']}|{udf1}|{udf2}|{udf3}|{udf4}|{udf5}|{udf6}|{udf7}|{udf8}|{udf9}|{udf10}|{SALT}"
        generated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

        # Payload Structure
        payload = {
            "key": str(MERCHANT_KEY).strip(),
            "txnid": str(txnid),
            "amount": str(amount),
            "productinfo": str(product_info_val),
            "firstname": str(validated_data['customer_name']).strip(),
            "email": str(validated_data['email']).strip(),
            "phone": str(validated_data['phone']).strip(),
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

        # Token handling & URL routing
        if response_json.get("status") == 1:
            access_key = response_json.get("data")
            checkout_url = f"{BASE_URL}/pay/{access_key}"
            
            # 📑 Audit log me update kar do ki link ban gaya
            db_log.response_payload = {
                "easebuzz_handshake_status": "TOKEN_GENERATED",
                "payment_url": checkout_url
            }
            db_log.save()
            
            return Response({
                "status": "success",
                "txnid": txnid,
                "payment_url": checkout_url
            }, status=status.HTTP_201_CREATED)
        else:
            db_log.status_code = 400
            db_log.response_payload = {"error": "Easebuzz rejection", "details": response_json}
            db_log.save()
            
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

        # Reverse Hash Formula Check
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
        
        # ------------------------------------------------------------------
        # 🤝 STEP 3: Handle Status and Sync with AllCloud on SUCCESS
        # ------------------------------------------------------------------
        if status_val and status_val.lower() == "success":
            transaction_obj.status = 'SUCCESS'
            transaction_obj.save()  # 🔥 updated_at automatic local Indian time ke sath save ho gaya

            # Dynamic log status update
            if transaction_obj.payment_log:
                db_log = transaction_obj.payment_log
                db_log.status_code = 200
                
                # 🇮🇳 Exact Indian Time Nikala Table Record se aur fractional seconds trim kiya
                local_indian_time = transaction_obj.updated_at.replace(tzinfo=None)
                clean_date = local_indian_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

                # 🔄 1. DB LOG KE REQUEST PAYLOAD ME REPAYMENT TIME STAMP UPDATE KIYA
                current_payload = db_log.request_payload
                if isinstance(current_payload, dict):
                    current_payload["ReceivedDate"] = clean_date  
                    db_log.request_payload = current_payload
                
                # 🔥 AllCloud Service ko call karne se pehle cache update committed kiya
                db_log.save() 

                # 🚀 AllCloud Repayment Payload (Ab exact PayU wale formats me mapping)
                allcloud_payload = {
                    "Amount": float(transaction_obj.amount),
                    "ReceivedDate": clean_date,                          # 🔥 Ekdum saaf localized datetime string
                    "AgreementNumber": transaction_obj.loan_ac_no,
                    "LoanReceiptMode": 2,                
                    "ChartOfAccountId": int(settings.ALLCLOUD_CHART_OF_ACCOUNT_ID),           
                    "PolicyPaymentTypeId": settings.ALLCLOUD_POLICY_PAYMENT_TYPE_ID  
                }

                # 🔥 Service class method call with parent_id for multi-user security mapping
                ac_response, ac_error = AllCloudService.save_repayment(allcloud_payload, parent_id=db_log.parent_id)

                # Tracking responses inside the centralized logs
                if ac_response:
                    db_log.response_payload = ac_response  # 🔥 Storing raw third-party json response direct
                else:
                    db_log.response_payload = {
                        "status": "success",
                        "response": f"transaction with {txnid} for amount {transaction_obj.amount} is success but AllCloud sync failed: {ac_error}"
                    }
                db_log.save()

            return redirect(
                f"{settings.FRONTEND_URL}/payment-success?"
                f"txnid={txnid}&amount={amount}&gateway=easebuzz"
            )

        # ❌ Agar Payment FAIL hui hai (FURL)
        else:
            transaction_obj.status = 'FAILED'
            transaction_obj.save()

            if transaction_obj.payment_log:
                db_log = transaction_obj.payment_log
                db_log.status_code = 400
                
                # 🎯 Centralized raw error status update
                db_log.response_payload = {
                    "status": "failed",
                    "response": f"transaction with {txnid} for amount {transaction_obj.amount} is failed via Easebuzz",
                    "raw_callback": request.data
                }
                db_log.save()

            return redirect(
                f"{settings.FRONTEND_URL}/payment-failure?"
                f"txnid={txnid}&amount={amount}&gateway=easebuzz"
            )
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)