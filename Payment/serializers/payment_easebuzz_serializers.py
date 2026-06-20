from rest_framework import serializers
from django.conf import settings
from Payment.model.payment_easebuzz import Transaction_easebuzz
from Payment.utils.sanitizer import sanitize_input


class TransactionEasebuzzSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction_easebuzz
        fields = ['amount', 'firstname', 'email', 'phone', 'productinfo']
        
    def validate_firstname(self, value):
        return sanitize_input(value, "firstname")

    def validate_productinfo(self, value):
        return sanitize_input(value, "productinfo")

    def validate_email(self, value):
        return sanitize_input(value, "email")

    def validate_phone(self, value):
        return sanitize_input(value, "phone")
    
    def validate_amount(self, value):
        min_amount = settings.EASEBUZZ_MIN_AMOUNT

        value = float(value)

        if value <= float(min_amount):
            raise serializers.ValidationError(
                f"Amount must be greater than {min_amount}"
            )

        return value
    