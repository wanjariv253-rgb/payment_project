from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Payment.services.all_cloud_service import AllCloudService

class RepaymentAPIView(APIView):
    
    def get(self, request):
        """
        Frontend se handle karega GET request.
        Query Params: ?agreement_no=1BERAR00005458304&finance_id=0
        """
        agreement_no = request.query_params.get('agreement_no')
        finance_id = request.query_params.get('finance_id', 0)

        if not agreement_no:
            return Response({"error": "agreement_no query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Service file ka function use kiya
        data, error = AllCloudService.get_repayment(agreement_no, finance_id)

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Frontend se handle karega POST request payment save karne ke liye.
        """
        payload = request.data  # Jo json frontend bhejega use collect kiya
        
        # Service file ka function use kiya
        data, error = AllCloudService.save_repayment(payload)

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)