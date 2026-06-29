from django.db import models

class GetPayment(models.Model):
    
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,  # <--- 🔥 Yahan 'on_null' ko badal kar 'on_delete' karo bhai
        blank=True, 
        null=True, 
        related_name='child_logs',
        help_text="Links child logs (Get/Post) to their parent log (Auth Token)"
    )

    # --- Pure Audit Logs Structure ---
    type = models.CharField(max_length=50, help_text="Auth Token, GetLoanDetails, or PostLoanDetails")
    request_payload = models.JSONField(default=dict, blank=True, null=True)   # Dynamic Request JSON
    response_payload = models.JSONField(default=dict, blank=True, null=True)  # Dynamic Response JSON
    status_code = models.IntegerField(blank=True, null=True, help_text="HTTP Status Code (e.g., 200, 400, 504)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_logs'

    def __str__(self):
        if self.parent:
            return f"Child Log ({self.type}) -> Parent ID: {self.parent.id} [HTTP {self.status_code or 'No Code'}]"
        return f"Parent Log ({self.type}) - ID: {self.id} [HTTP {self.status_code or 'No Code'}]"