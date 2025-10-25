from django.db import models

class Restaurant(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ["order", "name"]
    def __str__(self):
        return self.name

class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to="menu/", blank=True, null=True)
    def __str__(self):
        return f"{self.title} - ₹{self.price}"

class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("stripe", "Card (Stripe)"),
        ("cod", "Cash on Delivery"),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=12)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default="stripe")

    def __str__(self):
        pm = dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)
        return f"Order #{self.pk} - ₹{self.amount} - {pm} - {'PAID' if self.paid else 'UNPAID'}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    def line_total(self):
        return self.quantity * self.unit_price
    def __str__(self):
        return f"{self.menu_item.title} x {self.quantity}"
