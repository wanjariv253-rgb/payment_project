from django.db import models

class Transaction_easebuzz(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    txnid = models.CharField(max_length=100, unique=True, verbose_name="Transaction ID")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount")
    customer_name = models.CharField(max_length=100, verbose_name="First Name")
    loan_ac_no = models.CharField(max_length=50)
    city = models.CharField(max_length=100, null= True, blank= True)
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=15, verbose_name="Phone Number")
    productinfo = models.TextField(verbose_name="Product Information")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Transaction Status")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'payment_easebuzz'  
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.txnid} - {self.status}"