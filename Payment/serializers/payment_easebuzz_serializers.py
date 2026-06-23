import re

from rest_framework import serializers
from django.conf import settings
from Payment.model.payment_easebuzz import Transaction_easebuzz
from Payment.utils.sanitizer import sanitize_input


class TransactionEasebuzzSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction_easebuzz
        fields = [ 'loan_ac_no', 'customer_name', 'city', 'amount', 'email', 'phone', 'productinfo' ]
        
    def validate_customer_name(self, value):
        return sanitize_input(value, "customer_name")
    
    def validate_city(self, value):
     return sanitize_input(value, "city")
 
    def validate_loan_ac_no(self, value):
        return sanitize_input(value, "loan_ac_no")

    def validate_productinfo(self, value):
        return sanitize_input(value, "productinfo")

    def validate_email(self, value):
        value = sanitize_input(value, "email")

        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        if not re.match(email_pattern, value):
            raise serializers.ValidationError(
                "Enter a valid email address."
            )

        return value

    def validate_phone(self, value):
        value = sanitize_input(value, "phone")

        if not re.match(r'^[6-9]\d{9}$', value):
            raise serializers.ValidationError(
                "Enter a valid 10 digit mobile number."
            )

        if len(set(value)) == 1:
            raise serializers.ValidationError(
                "Invalid mobile number."
            )

        return value
    
    def validate_amount(self, value):
        min_amount = settings.EASEBUZZ_MIN_AMOUNT
        value = float(value)

        if value <= float(min_amount):
            raise serializers.ValidationError(
                f"Amount must be greater than {min_amount}"
            )

        return value
    