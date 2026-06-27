import hashlib
import uuid
import requests
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

        # 📑 STEP 1: central log me record banaya (Type 3: PostLoanDetails)
        db_log = GetPayment.objects.create (
            type=PaymentLogTypes.POST_LOAN_DETAILS,
            request_payload=request.data,
            response_payload={"info": "Initiated PayU process"},
            status_code=201,
            status='PENDING'
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
            "productinfo": validated_data['productinfo'], "firstname": validated_data['customer_name'],
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
        payu_hash = request.data.get('hash')
        # ... baaki fields extraction aur hash check validation as-is ...

        try:
            transaction_obj = Transaction.objects.get(txnid=txnid)
        except Transaction.objects.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # 🤝 STEP 3: Agar Payment actual me SUCCESS hui hai
        if status_val and status_val.lower() == "success":
            transaction_obj.status = 'SUCCESS'
            transaction_obj.save()

            if transaction_obj.payment_log:
                db_log = transaction_obj.payment_log
                db_log.status = 'SUCCESS'
                db_log.status_code = 200
                db_log.save()

                # 🚀 TUMNHE JO PAYLOAD BHEJNA HAI ALLCLOUD KO:
                allcloud_payload = {
                    "AgreementNumber": transaction_obj.loan_ac_no,
                    "Amount": float(transaction_obj.amount),
                    "CustomerName": transaction_obj.customer_name,
                    "Email": transaction_obj.email,
                    "MobileNo": transaction_obj.phone,
                    "VoucherNo": f"VCH-{txnid}",
                    "Notes": f"Paid successfully via PayU. Log ID: {db_log.id}"
                }

                # 🔥 TUMHARA SERVICE FUNCTION DIRECTLY CALL HUA:
                ac_response, ac_error = AllCloudService.save_repayment(allcloud_payload)

                # Response payload ko audit logs me back-up save kar lo
                if ac_response:
                    db_log.response_payload = {"allcloud_status": "SYNCED", "data": ac_response}
                else:
                    db_log.response_payload = {"allcloud_status": "FAILED_TO_SYNC", "error": ac_error}
                db_log.save()

            return redirect(f"{settings.FRONTEND_URL}/payment-success?txnid={txnid}&amount={transaction_obj.amount}")

        else:
            # Payment failed logic
            transaction_obj.status = 'FAILED'
            transaction_obj.save()
            if transaction_obj.payment_log:
                db_log = transaction_obj.payment_log
                db_log.status = 'FAILED'
                db_log.status_code = 400
                db_log.response_payload = {"error": "Gateway declared failure", "raw": request.data}
                db_log.save()

            return redirect(f"{settings.FRONTEND_URL}/payment-failure?txnid={txnid}&amount={transaction_obj.amount}")

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)