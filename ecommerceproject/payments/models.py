from django.db import models
from orders.models import Order

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('bkash', 'BKash'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', db_index=True)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"

    class Meta:
        ordering = ['-created_at']
