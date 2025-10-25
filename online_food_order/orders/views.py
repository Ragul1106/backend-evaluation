from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.contrib import messages

import stripe

from .models import MenuItem, Category, Restaurant, Order, OrderItem
from .forms import CheckoutForm
from .utils import get_cart, cart_add, cart_remove, cart_clear, cart_totals
from .utils import cart_change_qty, cart_set_qty


def home(request):
    restaurants = Restaurant.objects.all()
    categories = Category.objects.all()
    items = MenuItem.objects.filter(is_active=True)[:8]
    return render(request, "orders/layout/home.html", {
        "restaurants": restaurants,
        "categories": categories,
        "items": items,
    })


def menu(request):
    categories = Category.objects.all()
    selected_cat = request.GET.get("category")
    items = MenuItem.objects.filter(is_active=True)
    if selected_cat:
        items = items.filter(category_id=selected_cat)
    return render(request, "orders/layout/menu.html", {
        "categories": categories,
        "items": items,
        "selected_cat": selected_cat,
    })


def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id, is_active=True)
    qty = int(request.GET.get("qty", 1))
    cart_add(request.session, item.id, item.title, item.price, qty)
    messages.success(request, f"Added {item.title} to cart.")
    return redirect(request.META.get("HTTP_REFERER", "orders:menu"))


def remove_from_cart(request, item_id):
    cart_remove(request.session, item_id)
    messages.info(request, "Removed item from cart.")
    return redirect("orders:cart")


def cart_view(request):
    cart = get_cart(request.session)
    total, _ = cart_totals(request.session)
    detailed = []
    for item_id, data in cart.items():
        detailed.append({
            "id": int(item_id),
            "title": data["title"],
            "price": Decimal(data["price"]),
            "qty": data["qty"],
            "subtotal": Decimal(data["price"]) * data["qty"],
        })
    return render(request, "orders/layout/cart.html", {"cart_items": detailed, "total": total})


def _create_order_from_cart(request, checkout_data, payment_method):
    """Helper: create an Order + OrderItems from current session cart."""
    cart = get_cart(request.session)
    total_amount = Decimal("0.00")
    for v in cart.values():
        total_amount += Decimal(v["price"]) * int(v["qty"])

    order = Order.objects.create(
        name=checkout_data["name"],
        email=checkout_data["email"],
        address=checkout_data["address"],
        city=checkout_data["city"],
        pincode=checkout_data["pincode"],
        amount=total_amount,
        paid=False,
        payment_method=payment_method,
    )
    for key, v in cart.items():
        item = get_object_or_404(MenuItem, pk=int(key))
        OrderItem.objects.create(
            order=order,
            menu_item=item,
            quantity=int(v["qty"]),
            unit_price=Decimal(v["price"]),
        )
    return order


def checkout(request):
    cart = get_cart(request.session)
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect("orders:menu")

    total, _ = cart_totals(request.session)
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            checkout_data = form.cleaned_data
            payment_method = checkout_data.pop("payment_method")

            if payment_method == "cod":
                # Create order as COD (unpaid), clear cart, go to success page
                order = _create_order_from_cart(request, checkout_data, payment_method="cod")
                cart_clear(request.session)
                messages.success(request, "Order placed with Cash on Delivery. Please keep cash ready on delivery.")
                # Render success page with COD flag
                return redirect(f"{reverse('orders:success')}?order_id={order.id}&cod=1")

            # else Stripe flow: save data then redirect to create session (GET)
            request.session["checkout_data"] = checkout_data
            return redirect("orders:create_checkout_session")
    else:
        form = CheckoutForm()

    return render(request, "orders/layout/checkout.html", {"form": form, "total": total})


def create_checkout_session(request):
    """Stripe: Accept GET after checkout() saved data; redirect to Stripe Checkout."""
    cart = get_cart(request.session)
    if not cart:
        return HttpResponseBadRequest("Empty cart")

    checkout_data = request.session.get("checkout_data")
    if not checkout_data:
        return HttpResponseBadRequest("Missing checkout data")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    line_items = []
    for _, v in cart.items():
        price = Decimal(v["price"])
        qty = int(v["qty"])
        line_items.append({
            "price_data": {
                "currency": "inr",
                "product_data": {"name": v["title"]},
                "unit_amount": int(price * 100),
            },
            "quantity": qty,
        })

    # Create unpaid order tagged as Stripe
    order = _create_order_from_cart(request, checkout_data, payment_method="stripe")

    success_url = (
        request.build_absolute_uri(reverse("orders:success"))
        + f"?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}"
    )
    cancel_url = request.build_absolute_uri(reverse("orders:cancel"))

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])

    return redirect(session.url)


def success(request):
    # Handle either Stripe return OR COD redirect
    cod = request.GET.get("cod")  # "1" if COD path
    order_id = request.GET.get("order_id")
    if not order_id:
        messages.error(request, "Invalid order reference.")
        return redirect("orders:menu")

    if cod:
        order = get_object_or_404(Order, pk=order_id)
        # For COD, keep paid=False, just show success info
        payment_status = "cod"
        return render(request, "orders/layout/success.html", {"order": order, "payment_status": payment_status})

    # Stripe verification
    session_id = request.GET.get("session_id")
    if not session_id:
        messages.error(request, "Invalid payment confirmation.")
        return redirect("orders:menu")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.get("payment_status")
    except Exception:
        payment_status = None

    order = get_object_or_404(Order, pk=order_id, stripe_session_id=session_id)
    if payment_status == "paid":
        order.paid = True
        order.save(update_fields=["paid"])
        cart_clear(request.session)
        messages.success(request, "Payment successful! Your order is confirmed.")
    else:
        messages.warning(request, "Payment pending or failed. If charged, you'll receive confirmation soon.")

    return render(request, "orders/layout/success.html", {"order": order, "payment_status": payment_status})


def cancel(request):
    messages.info(request, "Payment canceled.")
    return render(request, "orders/layout/cancel.html")


def increase_qty(request, item_id):
    cart_change_qty(request.session, item_id, +1)
    return redirect("orders:cart")

def decrease_qty(request, item_id):
    cart_change_qty(request.session, item_id, -1)
    return redirect("orders:cart")
