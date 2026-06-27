from django.db import models

class GetPayment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    # --- Pure Audit Logs Structure ---
    type = models.CharField(max_length=50, help_text="Auth Token, GetLoanDetails, or PostLoanDetails")
    request_payload = models.JSONField(default=dict, blank=True, null=True)   # Dynamic Request JSON
    response_payload = models.JSONField(default=dict, blank=True, null=True)  # Dynamic Response JSON
    status_code = models.IntegerField(blank=True, null=True, help_text="HTTP Status Code (e.g., 200, 400, 504)")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    class Meta:
        db_table = 'payment_logs'

    def __str__(self):
        return f"{self.type} - [HTTP {self.status_code or 'No Code'}] at {self.created_at}"