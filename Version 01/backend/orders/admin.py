from django.contrib import admin
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model         = OrderItem
    extra         = 0
    fields        = ['product', 'quantity', 'price', 'subtotal']
    readonly_fields = ['subtotal']


class PaymentInline(admin.StackedInline):
    """StackedInline shows fields vertically instead of in a table — better for Payment."""
    model  = Payment
    extra  = 0
    fields = ['payment_method', 'amount', 'status', 'stripe_payment_id', 'paid_at']
    readonly_fields = ['paid_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ['id', 'user', 'status', 'total_amount', 'created_at']
    list_filter     = ['status', 'created_at']
    search_fields   = ['user__username', 'user__email']
    list_editable   = ['status']       # Change order status right from the list
    readonly_fields = ['created_at', 'updated_at']
    inlines         = [OrderItemInline, PaymentInline]

    fieldsets = (
        ('Order Info',  {'fields': ('user', 'status', 'total_amount')}),
        ('Delivery',    {'fields': ('shipping_address', 'notes')}),
        ('Timestamps',  {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = ['order', 'product', 'quantity', 'price', 'subtotal']
    search_fields = ['order__id', 'product__name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['order', 'payment_method', 'amount', 'status', 'paid_at']
    list_filter   = ['payment_method', 'status']
    search_fields = ['order__id', 'stripe_payment_id']
    readonly_fields = ['paid_at', 'created_at']
