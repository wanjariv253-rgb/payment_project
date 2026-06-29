import hashlib
import uuid
import requests
from datetime import datetime  # <-- 🔥 Date format ke liye import kiya
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import redirect
from Payment.constants import PaymentLogTypes
from Payment.model.get_payment import GetPayment
from Payment.serializers.payment_payu_serializer import TransactionInitiateSerializer
from Payment.model.payment_payu import Transaction  
from django.conf import settings

from Payment.services.all_cloud_service import AllCloudService

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
        
        validated_data = serializer.validated_data
        amount = validated_data['amount']

        # 🔄 FRONTEND SE PARENT LOG ID NIKALI
        parent_id = request.data.get('parent_log_id')

        # 🎯 CUSTOM PAYLOAD STRUCTURE FOR LOGS
        custom_log_payload = {
            "ChartOfAccountId": int(settings.ALLCLOUD_CHART_OF_ACCOUNT_ID),
            "AgreementNumber": validated_data.get('loan_ac_no'),  # Get se jo agreement no aaya
            "ReceivedDate": datetime.utcnow().isoformat() + "Z",   
            "Amount": float(amount),
            "LoanReceiptMode": 2,                                 # Constant Fix 2
            "PolicyPaymentTypeId": settings.ALLCLOUD_POLICY_PAYMENT_TYPE_ID
        }

        # 📑 STEP 1: Central log me custom format ke sath record banaya
        db_log = GetPayment.objects.create(
            parent_id=parent_id,
            type=PaymentLogTypes.POST_LOAN_DETAILS,
            request_payload=custom_log_payload,  # 🔥 Pura data badal kar custom payload daal diya
            response_payload={"info": "Initiated PayU process"},
            status_code=201
        )

        txnid = f"Txn{uuid.uuid4().hex[:10].upper()}"
        
        # 📑 STEP 2: payu table me data save kiya linked with log_id
        serializer.save(txnid=txnid, status='PENDING', payment_log=db_log)
        
        # Cryptographic Hash & PayU Handshake
        surl = settings.PAYU_SUCCESS_URL
        furl = settings.PAYU_FAILURE_URL
        hash_string = f"{PAYU_KEY}|{txnid}|{amount}|{validated_data['productinfo']}|{validated_data['customer_name']}|{validated_data['email']}|||||||||||{PAYU_SALT}"
        generated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

        payload = {
            "key": PAYU_KEY, "txnid": txnid, "amount": str(amount),
            "productinfo": validated_data['productinfo'], 
            "firstname": validated_data['customer_name'],
            "email": validated_data['email'], "phone": validated_data['phone'],
            "surl": surl, "furl": furl, "hash": generated_hash
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payu_response = requests.post(PAYU_URL, data=payload, headers=headers, allow_redirects=False)

        redirect_url = payu_response.headers.get('Location') if payu_response.status_code in [301, 302, 303] else payu_response.url

        db_log.response_payload = {"payment_url": redirect_url, "payu_handshake_status": "TOKEN_GENERATED"}
        db_log.save()

        return Response({
            "status": "success",
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
        status_val = request.data.get('status') 
        
        try:
            transaction_obj = Transaction.objects.get(txnid=txnid)
        except Transaction.objects.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # 🤝 STEP 3: Agar Payment actual me SUCCESS hui hai (SURL)
        if status_val and status_val.lower() == "success":
            transaction_obj.status = 'SUCCESS'
            transaction_obj.save()  # 🔥 Yahan updated_at automatic local timestamp ke sath save ho gaya

            if transaction_obj.payment_log:
                db_log = transaction_obj.payment_log
                db_log.status_code = 200
                
                # 🇮🇳 Jo time table me update hua (e.g., 2026-06-27 13:25:20.963514+05:30), 
                # uska timezone replace karke direct saaf Indian format string banayi:
                local_indian_time = transaction_obj.updated_at.replace(tzinfo=None)
                clean_date = local_indian_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] # Output: 2026-06-27T13:25:20.963

                # 🔄 1. DB LOG KE REQUEST PAYLOAD ME BHI SAME EXACT VALUE OVERWRITE KI
                current_payload = db_log.request_payload
                if isinstance(current_payload, dict):
                    current_payload["ReceivedDate"] = clean_date  
                    db_log.request_payload = current_payload
                
                # 🔥 AllCloud Service ko call karne se pehle db_log ko save kiya taaki data cache me sync ho jaye
                db_log.save() 

                # 🚀 AllCloud Repayment Payload (Exact table time format)
                allcloud_payload = {
                    "Amount": float(transaction_obj.amount),
                    "ReceivedDate": clean_date,                          # 🔥 Ab jayega ekdum perfect 13:25:20 wala local time
                    "AgreementNumber": transaction_obj.loan_ac_no,
                    "LoanReceiptMode": 2,                
                    "ChartOfAccountId": int(settings.ALLCLOUD_CHART_OF_ACCOUNT_ID),           
                    "PolicyPaymentTypeId": settings.ALLCLOUD_POLICY_PAYMENT_TYPE_ID  
                }

                # Service hit
                ac_response, ac_error = AllCloudService.save_repayment(allcloud_payload, parent_id=db_log.parent_id)

                # 🎯 2. DATABASE LOG RESPONSE UPDATE
                if ac_response:
                    db_log.response_payload = ac_response
                else:
                    db_log.response_payload = {
                        "status": "success",
                        "response": f"transaction with {txnid} for amount {transaction_obj.amount} is success but AllCloud sync failed: {ac_error}"
                    }
                
                db_log.save()

            return redirect(f"{settings.FRONTEND_URL}/payment-success?txnid={txnid}&amount={transaction_obj.amount}")

        # ❌ Agar Payment FAIL hui hai (FURL)
        else:
            transaction_obj.status = 'FAILED'
            transaction_obj.save()
            
            if transaction_obj.payment_log:
                db_log = transaction_obj.payment_log
                db_log.status_code = 400
                
                # 🎯 FAILURE ME PURANA HAI WAHI RAKHA
                db_log.response_payload = {
                    "status": "failed",
                    "response": f"transaction with {txnid} for amount {transaction_obj.amount} is failed"
                }
                db_log.save()

            return redirect(f"{settings.FRONTEND_URL}/payment-failure?txnid={txnid}&amount={transaction_obj.amount}")

    except Exception as main_e:
        # Pura fallback handle karne ke liye agar kuch crash ho jaye
        return Response({"error": str(main_e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
