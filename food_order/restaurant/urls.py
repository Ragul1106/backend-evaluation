from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    path('', views.menu_list, name='menu'),
    path('restaurants/', views.menu_list, name='restaurants'),
    path('restaurant/<int:restaurant_id>/', views.menu_list, name='menu_by_restaurant'),
    path('item/<int:pk>/', views.menu_item_detail, name='menu_item'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/<int:restaurant_id>/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
]
