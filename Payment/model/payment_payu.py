from django.db import models

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    txnid = models.CharField(max_length=100, unique=True)
    loan_ac_no = models.CharField(max_length=50)
    city = models.CharField(max_length=100, null= True, blank= True)
    # firstname = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)

    email = models.EmailField()
    phone = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    productinfo = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_payu'

    def __str__(self):
        return f"{self.txnid} - {self.amount} - {self.status}"