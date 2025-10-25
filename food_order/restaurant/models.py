from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Restaurant(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} — {self.restaurant.name}"

class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, related_name='menu_items', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='items', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_images/', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"

ORDER_STATUS_CHOICES = [
    ('PENDING','Pending'),
    ('PREPARING','Preparing'),
    ('READY','Ready for pickup/delivery'),
    ('COMPLETED','Completed'),
    ('CANCELLED','Cancelled'),
]

class Order(models.Model):
    restaurant = models.ForeignKey(Restaurant, related_name='orders', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    total = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} — {self.restaurant.name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)  # copy of price at order-time

    def __str__(self):
        return f"{self.quantity} × {self.menu_item.name}"
