import requests
from django.conf import settings
from Payment.constants import AllCloudEndpoints, PaymentLogTypes
from Payment.model.get_payment import GetPayment
class AllCloudService:
    @staticmethod
    def generate_token():
        headers = {
            'url': f"{settings.ALLCLOUD_API_BASE_URL}{AllCloudEndpoints.GET_BRANCH}",
            'appid': settings.ALLCLOUD_APP_ID,
            'usertoken': settings.ALLCLOUD_USER_TOKEN,
            'secrettoken': settings.ALLCLOUD_SECRET_TOKEN,
            'x-api-key': settings.ALLCLOUD_X_API_KEY,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(settings.ALLCLOUD_AUTH_URL, headers=headers, json={})
            
            token_text = response.text.strip()
            if token_text.startswith('"') and token_text.endswith('"'):
                token_text = token_text[1:-1]
                
            # Log Success with actual HTTP Status Code (200)
            GetPayment.objects.create(
                type=PaymentLogTypes.AUTH_TOKEN,
                request_payload={"info": "Token Request Sent"},
                response_payload={"token": f"{token_text[:15]}..."},
                status_code=response.status_code  # Save 200
            )
            return token_text
                
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if e.response else str(e)
            code = e.response.status_code if e.response else 500
            
            # Log Failure with exact error code (like 504, 401, etc.)
            GetPayment.objects.create(
                type=PaymentLogTypes.AUTH_TOKEN,
                request_payload={"info": "Token Request Failed"},
                response_payload={"error": error_text},
                status_code=code
            )
            return None

    @classmethod
    def get_repayment(cls, agreement_no, finance_id=0):
        
        full_auth_string = cls.generate_token()
        
        if not full_auth_string or "Error" in full_auth_string:
            return None, f"Token failed: {full_auth_string}"

        # AB DHYAN DO: 'amx ...' generate_token se hi aa raha hai, toh hum use DIRECT pass karenge!
        headers = {
            'accept': 'text/plain',
            'Authorization': full_auth_string  
        }
        params = {
            'AgreementNo': agreement_no,
            'FinanceId': finance_id
        }
        url = f"{settings.ALLCLOUD_API_BASE_URL}/Repayment/GetRepayment"

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json(), None
            return None, f"API Error: {response.text}"
        except requests.exceptions.RequestException as e:
            return None, str(e)

    @classmethod
    def save_repayment(cls, payload):
        full_auth_string = cls.generate_token()
        
        if not full_auth_string or "Error" in full_auth_string:
            return None, f"Token failed: {full_auth_string}"

        headers = {
            'Content-Type': 'application/json',
            'accept': 'text/plain',
            'Authorization': full_auth_string
        }
        url = f"{settings.ALLCLOUD_API_BASE_URL}/Repayment/SaveRepayment"

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json(), None
            return None, f"API Error: {response.text}"
        except requests.exceptions.RequestException as e:
            return None, str(e)