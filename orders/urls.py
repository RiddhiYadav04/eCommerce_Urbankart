from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
]