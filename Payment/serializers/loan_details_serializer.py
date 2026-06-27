from rest_framework import serializers


class LoanSerializer(serializers.Serializer):

    loan_ac_no = serializers.CharField(max_length=30)