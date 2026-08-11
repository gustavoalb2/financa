from django.contrib import admin
from .models import UserProfile, Category, Transaction, Product

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'initial_balance', 'currency')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'color', 'icon', 'user', 'is_default')
    list_filter = ('type', 'is_default')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'unit', 'cost_price', 'sale_price', 'user')
    search_fields = ('name', 'sku')
    list_filter = ('unit',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'type', 'amount', 'date', 'category', 'user', 'affects_stock', 'product', 'quantity')
    list_filter = ('type', 'date', 'category', 'payment_method', 'affects_stock')
    search_fields = ('description', 'notes')

