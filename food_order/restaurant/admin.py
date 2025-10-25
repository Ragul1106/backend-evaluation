from django.contrib import admin
from .models import Restaurant, Category, MenuItem, Order, OrderItem

class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name','phone','owner','created')
    inlines = [CategoryInline, MenuItemInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','restaurant','order')
    list_filter = ('restaurant',)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name','restaurant','price','is_available')
    list_filter = ('restaurant','is_available','category')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('price',)
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','restaurant','user','status','total','created')
    list_filter = ('status','restaurant')
    inlines = [OrderItemInline]
