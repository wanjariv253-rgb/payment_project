from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Payment.services.all_cloud_service import AllCloudService
from Payment.model.get_payment import GetPayment
from Payment.constants import PaymentLogTypes

class FetchRepaymentAPIView(APIView):
    """
    Method: GET | Type: GetLoanDetails
    """
    def get(self, request):
        agreement_no = request.query_params.get('agreement_no')
        finance_id = request.query_params.get('finance_id', 0)

        if not agreement_no:
            return Response({"error": "agreement_no parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Third-party call
        data, error = AllCloudService.get_repayment(agreement_no, finance_id)

        if error:
            # Agar fail hua toh code 400 ya jo bhi return ho raha hai save karo
            GetPayment.objects.create(
                type=PaymentLogTypes.GET_LOAN_DETAILS,
                request_payload={"agreement_no": agreement_no, "finance_id": finance_id},
                response_payload={"error": error},
                status_code=400
            )
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        # Success Log Entry with HTTP 200
        GetPayment.objects.create(
            type=PaymentLogTypes.GET_LOAN_DETAILS,
            request_payload={"agreement_no": agreement_no, "finance_id": finance_id},
            response_payload=data,
            status_code=200
        )
        
        return Response({
            "allcloud_data": data
        }, status=status.HTTP_200_OK)


# class CreatePaymentLogAPIView(APIView):
#     """
#     Method: POST | Type: PostLoanDetails
#     Purpose: Frontend form se extra details (Name, Email, Mobile, etc.) lekar audit trail banana
#     """
#     def post(self, request):
#         payload = request.data
        
#         # --- Required Fields Extraction ---
#         agreement_no = payload.get('agreement_no')
#         payment_status = payload.get('status')       # SUCCESS ya FAILED
#         customer_name = payload.get('CustomerName')
#         emi_amount = payload.get('EmiAmount')
#         email = payload.get('Email')
#         mobile_no = payload.get('Mobile_no')

#         # --- Validation Block ---
#         # Jo bhi fields tum compulsory rakhna chahte ho unhe yahan check karo
#         if not all([agreement_no, payment_status, customer_name, emi_amount]):
#             return Response(
#                 {"error": "Missing required fields! Ensure agreement_no, status, CustomerName, and EmiAmount are sent."}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             # Payment record initially created from frontend request (HTTP 201)
#             # Poora 'payload' dictionary directly request_payload column me chala jayega!
#             db_log = GetPayment.objects.create(
#                 type=PaymentLogTypes.POST_LOAN_DETAILS,
#                 request_payload=payload, 
#                 response_payload={
#                     "gateway_status_received": payment_status,
#                     "customer_info": {
#                         "email": email,
#                         "mobile": mobile_no
#                     }
#                 },
#                 status_code=201
#             )

#             # Agar payment status SUCCESS hai, toh AllCloud par transaction sync karne ka block
#             if payment_status == "SUCCESS":
#                 allcloud_payload = {
#                     "AgreementNumber": agreement_no,
#                     "CustomerName": customer_name,
#                     "Amount": float(emi_amount),
#                     "Email": email,
#                     "MobileNo": mobile_no,
#                     "Notes": f"Payment verified via gateway. Log ID: {db_log.id}"
#                 }
#                 print("SYNCING WITH ALLCLOUD PAYLOAD:", allcloud_payload)
                
#                 # AllCloud Service dynamic implementation yahan call hogi:
#                 res, err = AllCloudService.save_repayment(allcloud_payload)
#                 if res:
#                     db_log.status_code = 200 # Final post-sync success status
#                     db_log.response_payload = res
#                     db_log.save()

#             return Response({
#                 "message": "payload log created successfully!",
#                 "log_id": db_log.id,
#                 "status_code_logged": db_log.status_code
#             }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        