import hashlib
import uuid
import requests
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from Payment.serializers.payment_payu_serializer import TransactionInitiateSerializer
from Payment.model.payment_payu import Transaction  

# PayU Credentials
PAYU_KEY = "Qkm0KL"
PAYU_SALT = "vr5oKKUX81L48eEfW3CUoJuikBPfEKBR"
PAYU_URL = "https://test.payu.in/_payment"  # Standard Checkout endpoint

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
        amount = validated_data['amount']
        firstname = validated_data['firstname']
        email = validated_data['email']
        phone = validated_data['phone']
        productinfo = validated_data['productinfo']

        # Unique Txn ID aur DB Insertion
        txnid = f"Txn{uuid.uuid4().hex[:10].upper()}"
        serializer.save(txnid=txnid, status='PENDING')
        
        # Local Webhook/Callback Endpoints
        surl = "http://127.0.0.1:8000/api/payment/success/"
        furl = "http://127.0.0.1:8000/api/payment/failure/"

        # Cryptographic Hash
        hash_string = f"{PAYU_KEY}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{PAYU_SALT}"
        generated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

        # Payload Structure
        payload = {
            "key": PAYU_KEY,
            "txnid": txnid,
            "amount": str(amount),
            "productinfo": productinfo,
            "firstname": firstname,
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
        # 1. Saara incoming data ek baar mein extract karo
        txnid = request.data.get('txnid')
        payu_hash = request.data.get('hash')
        status_val = request.data.get('status')  # PayU bhejega: 'success' ya 'failure'/'failed'
        amount = request.data.get('amount')
        firstname = request.data.get('firstname')
        email = request.data.get('email')
        productinfo = request.data.get('productinfo')
        key = request.data.get('key')

        if not txnid or not status_val:
            return Response({"error": "Data incomplete hai!"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Reverse Hash Verification (Dono cases ke liye secure check)
        # PayU formula dono ke liye same rehta hai, dynamic status_val string pass hogi
        reverse_hash_string = f"{PAYU_SALT}|{status_val}|||||||||||{email}|{firstname}|{productinfo}|{amount}|{txnid}|{key}"
        calculated_hash = hashlib.sha512(reverse_hash_string.encode('utf-8')).hexdigest().lower()

        if calculated_hash != payu_hash:
            return Response({"error": "Hash Mismatch! Security block."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Database se transaction record uthao
        try:
            transaction_obj = Transaction.objects.get(txnid=txnid)
        except Transaction.objects.DoesNotExist:
            return Response({"error": "Transaction not found in Database"}, status=status.HTTP_404_NOT_FOUND)

        # 4. DYNAMIC STATUS UPDATE (If-Else ka short logic)
        # Agar PayU se status 'success' aaya toh DB mein SUCCESS daalo, nahi toh FAILED
        if status_val == "success":
            transaction_obj.status = 'SUCCESS'
            db_status = "SUCCESS"
            api_response_status = "success"
        else:
            transaction_obj.status = 'FAILED'
            db_status = "FAILED"
            api_response_status = "failed"

        # Database mein save karo
        transaction_obj.save()

        # 5. Dynamic Response Jo Tumne Manga (Success par success, fail par fail)
        return Response({
            "status": api_response_status,
            "message": f"Transaction {txnid} marked as {db_status}."
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)