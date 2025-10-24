from django.urls import path
from . import views

app_name = 'shop'
urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/razorpay/create/', views.razorpay_create_order, name='razorpay_create_order'),
    path('payment/razorpay/verify/', views.razorpay_verify, name='razorpay_verify'),
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
    path('invoice/<int:order_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]
