from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Product
from .models import CartItem, WishlistItem
from django.contrib import messages
from django.http import JsonResponse
import json
import razorpay
from django.conf import settings
from orders.models import Order, OrderItem, ShippingAddress
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import send_mail
from twilio.rest import Client

# Create your views here.
# View Cart
@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.get_total_price() for item in cart_items)
    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

# Add to Cart
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect('cart')

# Remove from Cart
@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart')

# Update Cart via traditional POST
@login_required
def update_cart(request):
    if request.method == 'POST':
        for item in CartItem.objects.filter(user=request.user):
            qty_field = f'quantity_{item.id}'
            try:
                new_qty = int(request.POST.get(qty_field))
                if new_qty > 0:
                    item.quantity = new_qty
                    item.save()
                else:
                    item.delete()
            except (ValueError, TypeError):
                continue
        messages.success(request, "Cart updated.")
    return redirect('cart')

# Update single cart item via AJAX
@login_required
def update_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('id')
        quantity = int(data.get('quantity'))
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        cart_item.quantity = quantity
        cart_item.save()
        item_total = cart_item.get_total_price()
        cart_total = sum(i.get_total_price() for i in CartItem.objects.filter(user=request.user))
        return JsonResponse({
            'item_total': f"{item_total:.2f}",
            'cart_total': f"{cart_total:.2f}",
        })

# Wishlist
@login_required
def view_wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    return render(request, 'cart/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    WishlistItem.objects.get_or_create(user=request.user, product=product)
    messages.success(request, f"{product.name} added to your wishlist.")
    return redirect('wishlist')

@login_required
def remove_from_wishlist(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    item.delete()
    messages.success(request, "Item removed from wishlist.")
    return redirect('wishlist')

@login_required
def move_to_cart(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    CartItem.objects.get_or_create(user=request.user, product=item.product)
    item.delete()
    messages.success(request, f"{item.product.name} moved to cart.")
    return redirect('cart')

# Checkout with Razorpay
@login_required
def checkout(request):
    profile = request.user.userprofile
    required_fields = [profile.address, profile.city, profile.state, profile.postal_code, profile.phone]
    if not all(required_fields):
        messages.warning(request, "Please complete your shipping details before proceeding to checkout.")
        return redirect('profile')

    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    total_amount = sum(item.get_total_price() for item in cart_items)
    amount_paise = int(total_amount * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment = client.order.create({'amount': amount_paise, 'currency': 'INR', 'payment_capture': 1})

    return render(request, 'cart/checkout.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': payment['id']
    })

# Payment success handler (called by JS)
@csrf_exempt
@login_required
def payment_success(request):
    if request.method == "POST":
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items:
            messages.warning(request, "Your cart is already empty.")
            return redirect('cart')

        payment_id = request.POST.get("razorpay_payment_id")
        order_id = request.POST.get("razorpay_order_id")
        signature = request.POST.get("razorpay_signature")

        # Shipping from user profile
        profile = request.user.userprofile
        shipping = ShippingAddress.objects.create(
            user=request.user,
            address=profile.address,
            city=profile.city,
            state=profile.state,
            postal_code=profile.postal_code,
            phone=profile.phone
        )

        # Create order
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping,
            is_paid=True,
            payment_id=payment_id,
            shipping_status='Pending',
            created_at=timezone.now()
        )

        # Add order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.get_display_price()
            )

        # Send confirmation email
        send_mail(
            subject='Your UrbanKart Order Confirmation',
            message=f'Thank you {request.user.first_name}, your order #{order.id} has been placed!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        # Send SMS via Twilio
        def send_sms(to, body):
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=profile.phone
            )
            print("SMS sent:", message.sid)
        send_sms(profile.phone,
            f"Hi {request.user.first_name}, your UrbanKart order #{order.id} is confirmed!"
        )

        # Clear cart
        cart_items.delete()

        messages.success(request, "Payment successful and order placed!")
        return redirect('home')
    return redirect('cart')