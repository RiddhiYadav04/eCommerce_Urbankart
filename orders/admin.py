from django.contrib import admin
from .models import Order, OrderItem, ShippingAddress

# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'is_paid', 'shipping_status']
    list_filter = ['shipping_status', 'is_paid', 'created_at']
    search_fields = ['user__username', 'id']
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)
admin.site.register(ShippingAddress)