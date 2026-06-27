import requests
from django.conf import settings

class AllCloudService:
    @staticmethod
    def generate_token():
        """
        AllCloud se poora Auth string mangwane ke liye aur quotes saaf karne ke liye.
        """
        headers = {
            'url': 'https://uat-apiv2-berarfinance.allcloud.app/api/Branch/GetBranchByUserIdAsync',
            'appid': settings.ALLCLOUD_APP_ID,
            'usertoken': settings.ALLCLOUD_USER_TOKEN,
            'secrettoken': settings.ALLCLOUD_SECRET_TOKEN,
            'x-api-key': settings.ALLCLOUD_X_API_KEY,
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(settings.ALLCLOUD_AUTH_URL, headers=headers, json={})
            response.raise_for_status()
            
            token_text = response.text.strip()
            
            # AGAR RESPONSE ME SIDE ME QUOTES HAIN TO UNHE NIKAL DO
            if token_text.startswith('"') and token_text.endswith('"'):
                token_text = token_text[1:-1]
                
            print("CLEANED TOKEN BEING SENT TO GET API:", token_text)
            return token_text
                
        except requests.exceptions.RequestException as e:
            print(f"Token Generation Error: {e}")
            return None

    @classmethod
    def get_repayment(cls, agreement_no, finance_id=0):
        """
        Loan Account Details Fetch karne ke liye (GET Request).
        """
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
        """
        Repayment Save karne ke liye (POST Request).
        """
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