from rest_framework import serializers
from Payment.model.payment_payu import Transaction
from Payment.utils.sanitizer import sanitize_input
from django.conf import settings
from decimal import Decimal

class TransactionInitiateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [ 'loan_ac_no', 'customer_name', 'city', 'amount', 'email', 'phone', 'productinfo' ]

    def validate_customer_name(self, value):
        return sanitize_input(value, "customer_name")
    
    def validate_city(self, value):
     return sanitize_input(value, "city")
 
    def validate_loan_ac_no(self, value):
        return sanitize_input(value, "loan_ac_no")
    
    def validate_email(self, value):
        return sanitize_input(value, "email")

    def validate_phone(self, value):
        return sanitize_input(value, "phone")

    def validate_productinfo(self, value):
        return sanitize_input(value, "productinfo")

    def validate_amount(self, value):
        min_amount = Decimal(str(settings.PAYU_MIN_AMOUNT))

        value = Decimal(str(value))

        if value < min_amount:
            raise serializers.ValidationError(
                f"Amount must be greater than {min_amount}"
            )

        return value