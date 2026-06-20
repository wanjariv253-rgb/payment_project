from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def loan_details_test(request):
    loan_account_no = request.GET.get("loan_account_no")

    test_data = {
        "5222510": {
            "loan_account_no": "5222510",
            "customer_name": "PRASHANT CHANDRAKANT SHAHU",
            "city": "Nagpur",
            "vehicle_name": "PL",
        },
        "5222511": {
            "loan_account_no": "5222511",
            "customer_name": "RAHUL SHARMA",
            "city": "Pune",
            "vehicle_name": "CAR",
        }
    }

    if not loan_account_no:
        return Response(
            {"error": "loan_account_no is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    data = test_data.get(loan_account_no)

    if not data:
        return Response(
            {"error": "Loan Account Number not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        "status": "success",
        "data": data
    })