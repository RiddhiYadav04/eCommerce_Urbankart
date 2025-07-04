from django.db import models
from django.contrib.auth.models import User
from core.models import Product

# Create your models here.
class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.username}'s shipping address"


class Order(models.Model):
    SHIPPING_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_status = models.CharField(max_length=20, choices=SHIPPING_STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def get_total_cost(self):
        return sum(item.get_total_price() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # capture price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        return self.price * self.quantity