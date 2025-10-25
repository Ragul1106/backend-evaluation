from decimal import Decimal

CART_KEY = "cart"  # { item_id: {"title": str, "price": "123.45", "qty": int} }

def get_cart(session):
    return session.get(CART_KEY, {})

def save_cart(session, cart):
    session[CART_KEY] = cart
    session.modified = True

def cart_add(session, item_id, title, price, qty=1):
    cart = get_cart(session)
    item = cart.get(str(item_id), {"title": title, "price": str(price), "qty": 0})
    item["qty"] += int(qty)
    cart[str(item_id)] = item
    save_cart(session, cart)

def cart_remove(session, item_id):
    cart = get_cart(session)
    cart.pop(str(item_id), None)
    save_cart(session, cart)

def cart_clear(session):
    save_cart(session, {})

def cart_totals(session):
    cart = get_cart(session)
    total = Decimal("0.00")
    count = 0
    for v in cart.values():
        total += Decimal(v["price"]) * v["qty"]
        count += v["qty"]
    return total, count

def cart_change_qty(session, item_id, delta):
    cart = get_cart(session)
    key = str(item_id)
    if key in cart:
        cart[key]["qty"] = max(0, cart[key]["qty"] + int(delta))
        if cart[key]["qty"] == 0:
            cart.pop(key)
        save_cart(session, cart)

def cart_set_qty(session, item_id, qty):
    cart = get_cart(session)
    key = str(item_id)
    qty = int(qty)
    if qty <= 0:
        cart.pop(key, None)
    else:
        if key in cart:
            cart[key]["qty"] = qty
    save_cart(session, cart)

