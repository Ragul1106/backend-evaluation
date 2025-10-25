from django.contrib import admin
from .models import Restaurant, Category, MenuItem, Order, OrderItem

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "phone")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "restaurant", "category", "price", "is_active")
    list_filter = ("restaurant", "category", "is_active")
    search_fields = ("title",)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("menu_item", "quantity", "unit_price")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "name", "email", "amount", "payment_method", "paid")
    list_filter = ("paid", "payment_method", "created_at")
    readonly_fields = ("created_at", "amount", "stripe_session_id")
    inlines = [OrderItemInline]
