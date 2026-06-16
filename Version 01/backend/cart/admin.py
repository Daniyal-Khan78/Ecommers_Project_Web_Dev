from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model  = CartItem
    extra  = 0          # Don't show empty slots — just existing items
    fields = ['product', 'quantity', 'added_at']
    readonly_fields = ['added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display  = ['user', 'total_items', 'total_price', 'updated_at']
    search_fields = ['user__username', 'user__email']
    inlines       = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display  = ['cart', 'product', 'quantity', 'subtotal', 'added_at']
    search_fields = ['cart__user__username', 'product__name']
