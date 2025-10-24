from django.contrib import admin
from .models import Category, Product, Order, OrderItem, PaymentRecord

admin.site.register(Category)
admin.site.register(Product)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','fullname','email','status','created_at')
    inlines = [OrderItemInline]

admin.site.register(PaymentRecord)
