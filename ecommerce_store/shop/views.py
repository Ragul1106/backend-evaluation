import json, uuid, hmac, hashlib, base64
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Category, Order, OrderItem, PaymentRecord
from .forms import CheckoutForm
import razorpay
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from io import BytesIO

# ---------- CART (session-based) ----------
def _get_cart(request):
    return request.session.setdefault('cart', {})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return render(request, 'shop/product_list.html', {'products': category.products.all(), 'category': category})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'shop/product_detail.html', {'product': product})

def cart_view(request):
    cart = _get_cart(request)
    items = []
    total = 0
    for pid, qty in cart.items():
        try:
            product = Product.objects.get(pk=int(pid))
        except Product.DoesNotExist:
            continue
        items.append({'product': product, 'quantity': qty, 'line_total': product.price * qty})
        total += product.price * qty
    return render(request, 'shop/cart.html', {'items': items, 'total': total})

def cart_add(request, product_id):
    cart = _get_cart(request)
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session.modified = True
    return redirect('shop:cart')

def cart_remove(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    request.session.modified = True
    return redirect('shop:cart')

# ---------- CHECKOUT ----------
def checkout(request):
    cart = _get_cart(request)
    if not cart:
        return redirect('shop:product_list')
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            # create invoice number sequential-ish
            order.invoice_number = f'INV-{uuid.uuid4().hex[:8].upper()}'
            order.save()
            # create items
            for pid, qty in cart.items():
                product = Product.objects.get(pk=int(pid))
                OrderItem.objects.create(order=order, product=product, price=product.price, quantity=qty, gst_percent=product.gst_percent)
            request.session['last_order_id'] = order.id
            # choose payment later: provide choices in template
            return redirect('shop:checkout')  # to GET show payment options
    else:
        form = CheckoutForm()
    last_order_id = request.session.get('last_order_id')
    order = None
    if last_order_id:
        order = get_object_or_404(Order, pk=last_order_id)
    return render(request, 'shop/checkout.html', {'form': form, 'order': order, 'razorpay_key': settings.RAZORPAY_KEY_ID})

# ---------- RAZORPAY SERVER ORDER ----------
def razorpay_create_order(request):
    # expects order_id in POST
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    data = json.loads(request.body.decode())
    order_id = data.get('order_id')
    order = get_object_or_404(Order, pk=order_id)
    amount = int(order.total_amount() * 100)  # paise
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({'amount': amount, 'currency': 'INR', 'receipt': str(order.invoice_number)})
    PaymentRecord.objects.create(order=order, gateway='razorpay', gateway_order_id=razorpay_order.get('id'), amount=order.total_amount())
    return JsonResponse({'razorpay_order_id': razorpay_order.get('id'), 'amount': amount, 'key': settings.RAZORPAY_KEY_ID})

@csrf_exempt
def razorpay_verify(request):
    # Razorpay form will post payment details here to verify signature
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    payload = request.POST
    razorpay_payment_id = payload.get('razorpay_payment_id')
    razorpay_order_id = payload.get('razorpay_order_id')
    razorpay_signature = payload.get('razorpay_signature')
    # verify signature
    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_signature = hmac.new(bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'), msg=bytes(msg,'utf-8'), digestmod=hashlib.sha256).hexdigest()
    if generated_signature == razorpay_signature:
        # mark payment captured
        pr = PaymentRecord.objects.filter(gateway_order_id=razorpay_order_id, gateway='razorpay').first()
        if pr:
            pr.gateway_payment_id = razorpay_payment_id
            pr.captured = True
            pr.save()
            order = pr.order
            order.status = 'paid'
            order.save()
            request.session['cart'] = {}
            return redirect('shop:invoice_pdf', order_id=order.id)
    return HttpResponseForbidden('Signature verification failed')

@csrf_exempt
def razorpay_webhook(request):
    # verify webhook signature header 'X-Razorpay-Signature'
    import razorpay as rz
    from django.views.decorators.http import require_POST
    signature = request.headers.get('X-Razorpay-Signature', '')
    body = request.body
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        # verify webhook signature using razorpay utility
        client.utility.verify_webhook_signature(body, signature, settings.RAZORPAY_KEY_SECRET)
    except Exception:
        return HttpResponseForbidden('Invalid webhook signature')
    payload = json.loads(body.decode())
    event = payload.get('event')
    if event == 'payment.captured':
        rp = payload.get('payload', {}).get('payment', {}).get('entity', {})
        rz_order_id = rp.get('order_id')
        pr = PaymentRecord.objects.filter(gateway_order_id=rz_order_id, gateway='razorpay').first()
        if pr:
            pr.gateway_payment_id = rp.get('id')
            pr.captured = True
            pr.save()
            order = pr.order
            order.status = 'paid'
            order.save()
    return JsonResponse({'status': 'ok'})

# ---------- INVOICE PDF ----------
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    # ensure populated items
    context = {
        'order': order,
        'company_name': settings.COMPANY_NAME,
        'company_address': settings.COMPANY_ADDRESS,
        'company_gstin': settings.COMPANY_GSTIN,
    }
    html = render_to_string('shop/invoice.html', context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), dest=result)
    if pdf.err:
        return HttpResponse('PDF generation failed', status=500)
    resp = HttpResponse(result.getvalue(), content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="invoice_{order.invoice_number}.pdf"'
    return resp
