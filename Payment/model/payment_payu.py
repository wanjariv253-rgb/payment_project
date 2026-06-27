from django.db import models

from Payment.model.get_payment import GetPayment

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    payment_log = models.ForeignKey(
        GetPayment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='payu_transactions'
    )
    txnid = models.CharField(max_length=100, unique=True)
    loan_ac_no = models.CharField(max_length=50)
    city = models.CharField(max_length=100, null= True, blank= True)
    customer_name = models.CharField(max_length=100)

    email = models.EmailField()
    phone = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    productinfo = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_payu'

    def __str__(self):
        return f"{self.txnid} - {self.amount} - {self.status}"