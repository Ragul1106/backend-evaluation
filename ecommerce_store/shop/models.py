from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=4, decimal_places=2, default=18)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self): return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])

class Order(models.Model):
    STATUS_CHOICES = [('created','Created'),('paid','Paid'),('shipped','Shipped'),('cancelled','Cancelled')]
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    fullname = models.CharField(max_length=200)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    invoice_number = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self): return f'Order {self.id} - {self.fullname}'

    def total_amount(self):
        items = self.items.all()
        subtotal = sum([item.total_price_excl_tax() for item in items])
        total_tax = sum([item.tax_amount() for item in items])
        return subtotal + total_tax

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    gst_percent = models.DecimalField(max_digits=4, decimal_places=2, default=18)

    def total_price_excl_tax(self):
        return self.price * self.quantity

    def tax_amount(self):
        return (self.total_price_excl_tax() * self.gst_percent) / 100

class PaymentRecord(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    gateway = models.CharField(max_length=50)
    gateway_order_id = models.CharField(max_length=120, blank=True, null=True)
    gateway_payment_id = models.CharField(max_length=120, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    captured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
