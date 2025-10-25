from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.home, name="home"),
    path("menu/", views.menu, name="menu"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:item_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/increase/<int:item_id>/", views.increase_qty, name="increase_qty"),   # <---
    path("cart/decrease/<int:item_id>/", views.decrease_qty, name="decrease_qty"),   # <---
    path("checkout/", views.checkout, name="checkout"),
    path("create-checkout-session/", views.create_checkout_session, name="create_checkout_session"),
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
]
