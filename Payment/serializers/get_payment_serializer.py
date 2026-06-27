from rest_framework import serializers
from Payment.model.get_payment import GetPayment

class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GetPayment
        fields = '__all__'