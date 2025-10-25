from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction

from .models import Restaurant, MenuItem, Category, Order, OrderItem
from .forms import CheckoutForm

# --- session-cart helpers ---
def _get_cart(session):
    return session.get('cart', {})

def _save_cart(session, cart):
    session['cart'] = cart
    session.modified = True

# --- Views expected by urls.py ---

def menu_list(request, restaurant_id=None):
    """
    If restaurant_id provided, show that restaurant menu with categories.
    Otherwise show list of restaurants.
    """
    if restaurant_id:
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        categories = restaurant.categories.prefetch_related('items').all()
        return render(request, 'restaurant/menu_list.html', {
            'restaurant': restaurant,
            'categories': categories,
        })
    restaurants = Restaurant.objects.all()
    return render(request, 'restaurant/menu_list.html', {
        'restaurants': restaurants
    })


def menu_item_detail(request, pk):
    item = get_object_or_404(MenuItem, id=pk)
    return render(request, 'restaurant/menu_item.html', {'item': item})


def add_to_cart(request, item_id):
    cart = _get_cart(request.session)
    cart[str(item_id)] = cart.get(str(item_id), 0) + 1
    _save_cart(request.session, cart)
    messages.success(request, "Added to cart")
    # redirect back to referring page if available
    return redirect(request.META.get('HTTP_REFERER', reverse('restaurant:menu')))


def remove_from_cart(request, item_id):
    cart = _get_cart(request.session)
    if str(item_id) in cart:
        del cart[str(item_id)]
        _save_cart(request.session, cart)
    return redirect('restaurant:cart')


def cart_view(request):
    cart = _get_cart(request.session)
    items = []
    total = Decimal('0.00')
    for item_id, qty in cart.items():
        try:
            menu_item = MenuItem.objects.get(id=int(item_id))
        except MenuItem.DoesNotExist:
            continue
        line_total = menu_item.price * qty
        items.append({'menu_item': menu_item, 'quantity': qty, 'line_total': line_total})
        total += line_total
    return render(request, 'restaurant/cart.html', {'items': items, 'total': total})


@transaction.atomic
def checkout(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    cart = _get_cart(request.session)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('restaurant:menu_by_restaurant', restaurant_id=restaurant.id)

    def build_cart_items():
        items = []
        total = Decimal('0.00')
        for item_id, qty in cart.items():
            try:
                menu_item = MenuItem.objects.get(id=int(item_id))
            except MenuItem.DoesNotExist:
                continue
            lt = menu_item.price * qty
            items.append({'menu_item': menu_item, 'quantity': qty, 'line_total': lt})
            total += lt
        return items, total

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                restaurant=restaurant,
                user=request.user if request.user.is_authenticated else None,
                status='PENDING',
                address=form.cleaned_data.get('address', ''),
                phone=form.cleaned_data.get('phone', ''),
                total=0
            )
            total = Decimal('0.00')
            for item_id, qty in cart.items():
                try:
                    menu_item = MenuItem.objects.get(id=int(item_id))
                except MenuItem.DoesNotExist:
                    continue
                price = menu_item.price
                OrderItem.objects.create(order=order, menu_item=menu_item, quantity=qty, price=price)
                total += price * qty

            order.total = total
            order.status = 'PREPARING'
            order.save()

            request.session['cart'] = {}
            request.session.modified = True

            messages.success(request, "Payment successful — your order has been placed!")
            return redirect('restaurant:order_success', order_id=order.id)
        # if form invalid fall through to re-render
        items, total = build_cart_items()
        return render(request, 'restaurant/checkout.html', {
            'restaurant': restaurant, 'form': form, 'items': items, 'total': total
        })

    # GET
    form = CheckoutForm()
    items, total = build_cart_items()
    return render(request, 'restaurant/checkout.html', {
        'restaurant': restaurant, 'form': form, 'items': items, 'total': total
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'restaurant/order_success.html', {'order': order})
