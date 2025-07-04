from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_cart, name='cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/', views.update_cart, name='update_cart'),
    path('update-item/', views.update_cart_item, name='update_cart_item'),
    # Wishlist
    path('wishlist/', views.view_wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<int:item_id>/', views.move_to_cart, name='move_to_cart'),
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
]