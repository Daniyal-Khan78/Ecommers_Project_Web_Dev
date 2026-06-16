from django.db import transaction
from django.db.models import F
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Order, OrderItem, Payment
from .serializers import (
    OrderSerializer,
    PlaceOrderSerializer,
    OrderStatusUpdateSerializer,
)
from cart.models import Cart, CartItem
from utils.responses import success_response, error_response, paginated_response
from utils.permissions import IsAdminUser
from utils.notifications import send_notification


# ─── Pagination ───────────────────────────────────────────────────────────────
class OrderPagination(PageNumberPagination):
    page_size             = 10
    page_size_query_param = 'page_size'
    max_page_size         = 50


# ─── Notification messages for each status change ────────────────────────────
ORDER_NOTIFICATIONS = {
    Order.Status.CONFIRMED: (
        "Order Confirmed!",
        "Your order #{id} has been confirmed and is being prepared.",
        "order"
    ),
    Order.Status.SHIPPED: (
        "Order Shipped!",
        "Great news! Your order #{id} is on its way to you.",
        "order"
    ),
    Order.Status.DELIVERED: (
        "Order Delivered!",
        "Your order #{id} has been delivered. Enjoy your purchase!",
        "order"
    ),
    Order.Status.CANCELLED: (
        "Order Cancelled",
        "Your order #{id} has been cancelled. Contact support if this was a mistake.",
        "order"
    ),
}


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 1: PlaceOrderView
# POST /api/orders/create/
# ═════════════════════════════════════════════════════════════════════════════
class PlaceOrderView(APIView):
    """
    Converts the user's cart into a confirmed order.

    This is the most critical endpoint in the entire system.
    Every step must succeed together or none must persist.
    We use transaction.atomic() to guarantee this.

    Full placement flow:
      1. Validate request body (address, payment method)
      2. Load the user's cart
      3. Validate cart is not empty
      4. Lock all product rows with select_for_update()
      5. Validate every item has sufficient stock
      6. Calculate order total
      7. Create the Order record
      8. Create one OrderItem per cart item (with price snapshot)
      9. Decrement stock for each product using F() expressions
     10. Create a Payment record (status=pending)
     11. Clear the cart
     12. Send a confirmation notification to the user
     13. Return the full order
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # ── Step 1: Validate request body ────────────────────────────────────
        serializer = PlaceOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Please correct the errors before placing your order.",
                errors=serializer.errors
            )

        shipping_address = serializer.validated_data['shipping_address']
        payment_method   = serializer.validated_data['payment_method']
        notes            = serializer.validated_data.get('notes', '')

        # ── Step 2: Load the user's cart ──────────────────────────────────────
        try:
            cart = Cart.objects.prefetch_related(
                'items__product'
            ).get(user=request.user)
        except Cart.DoesNotExist:
            return error_response(
                message="Your cart could not be found. Please try again.",
                status_code=500
            )

        # ── Step 3: Validate cart is not empty ────────────────────────────────
        cart_items = list(cart.items.all())
        if not cart_items:
            return error_response(
                message="Your cart is empty. Add some products before checking out.",
                status_code=400
            )

        # ── Steps 4–12: All database writes in a single atomic transaction ────
        try:
            with transaction.atomic():

                # Step 4: select_for_update() locks the product rows.
                # Any other transaction trying to read these rows will WAIT
                # until our transaction completes. This prevents two customers
                # from both buying the last item in stock.
                product_ids = [item.product_id for item in cart_items]
                from products.models import Product
                locked_products = {
                    p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
                }

                # Step 5: Validate stock for every cart item
                stock_errors = []
                for item in cart_items:
                    product = locked_products.get(item.product_id)
                    if not product or not product.is_available:
                        stock_errors.append(
                            f"'{item.product.name}' is no longer available."
                        )
                    elif item.quantity > product.stock:
                        stock_errors.append(
                            f"'{product.name}': only {product.stock} left in stock, "
                            f"you have {item.quantity} in your cart."
                        )

                if stock_errors:
                    # Raise to trigger rollback, return error outside atomic block
                    raise ValueError('\n'.join(stock_errors))

                # Step 6: Calculate the total
                # Use the product's effective_price (discount if available)
                total_amount = sum(
                    locked_products[item.product_id].effective_price * item.quantity
                    for item in cart_items
                )

                # Step 7: Create the Order record
                order = Order.objects.create(
                    user             = request.user,
                    status           = Order.Status.PENDING,
                    total_amount     = total_amount,
                    shipping_address = shipping_address,
                    notes            = notes,
                )

                # Step 8: Create one OrderItem per cart item
                # We snapshot the price here — if the product price changes
                # tomorrow, this order will always show what was charged today.
                order_items = []
                for item in cart_items:
                    product = locked_products[item.product_id]
                    order_items.append(OrderItem(
                        order    = order,
                        product  = product,
                        quantity = item.quantity,
                        price    = product.effective_price,  # SNAPSHOT: current price
                    ))
                OrderItem.objects.bulk_create(order_items)

                # Step 9: Decrement stock using F() expression.
                # F('stock') - item.quantity runs as SQL:
                #   UPDATE products_product SET stock = stock - N WHERE id = X
                # This is safer than Python arithmetic because the subtraction
                # happens in a single database operation, not read-then-write.
                for item in cart_items:
                    from products.models import Product as Prod
                    Prod.objects.filter(id=item.product_id).update(
                        stock=F('stock') - item.quantity
                    )

                # Step 10: Create a Payment record (pending until Stripe confirms)
                Payment.objects.create(
                    order          = order,
                    payment_method = payment_method,
                    amount         = total_amount,
                    status         = Payment.PaymentStatus.PENDING,
                )

                # Step 11: Clear the cart (CartItem rows only — keep the Cart record)
                cart.items.all().delete()

                # Step 12: Send confirmation notification
                send_notification(
                    user    = request.user,
                    title   = "Order Placed Successfully!",
                    message = (
                        f"Your order #{order.id} for {len(cart_items)} item(s) "
                        f"totaling ${total_amount:.2f} has been received. "
                        f"We'll update you when it's confirmed."
                    ),
                    notification_type = 'order',
                    link  = f"/orders/{order.id}",
                )

        except ValueError as e:
            # Stock validation errors — raised inside atomic() to trigger rollback
            return error_response(
                message="Order could not be placed due to stock issues.",
                errors={"stock": str(e).split('\n')},
                status_code=400
            )
        except Exception as e:
            # Unexpected error — all changes rolled back by atomic()
            return error_response(
                message="An error occurred while placing your order. Please try again.",
                status_code=500
            )

        # Return the complete order details
        order_serializer = OrderSerializer(
            Order.objects.prefetch_related(
                'items__product__images',
                'items__product__category',
                'payment'
            ).get(pk=order.pk),
            context={'request': request}
        )

        return success_response(
            data=order_serializer.data,
            message=f"Order #{order.id} placed successfully! Total: ${total_amount:.2f}",
            status_code=201
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 2: OrderListView
# GET /api/orders/
# ═════════════════════════════════════════════════════════════════════════════
class OrderListView(APIView):
    """
    Returns the authenticated user's order history, newest first.
    Supports filtering by status: GET /api/orders/?status=shipped
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Order.objects.filter(
            user=request.user
        ).prefetch_related(
            'items__product__images',
            'items__product__category',
            'payment'
        ).order_by('-created_at')

        # Optional status filter: GET /api/orders/?status=pending
        status_filter = request.query_params.get('status')
        if status_filter and status_filter in dict(Order.Status.choices):
            queryset = queryset.filter(status=status_filter)

        paginator = OrderPagination()
        page      = paginator.paginate_queryset(queryset, request)
        serializer = OrderSerializer(page, many=True, context={'request': request})

        return paginated_response(
            paginator  = paginator,
            data       = serializer.data,
            message    = "Orders retrieved successfully."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 3: OrderDetailView
# GET /api/orders/<pk>/
# ═════════════════════════════════════════════════════════════════════════════
class OrderDetailView(APIView):
    """
    Returns the full details of one specific order.
    Users can only view their OWN orders — we filter by user in the query.
    """
    permission_classes = [IsAuthenticated]

    def _get_order(self, pk, user):
        try:
            return Order.objects.prefetch_related(
                'items__product__images',
                'items__product__category',
                'payment'
            ).get(pk=pk, user=user)  # user filter prevents viewing others' orders
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self._get_order(pk, request.user)
        if not order:
            return error_response(
                message="Order not found.",
                status_code=404
            )

        serializer = OrderSerializer(order, context={'request': request})
        return success_response(
            data    = serializer.data,
            message = f"Order #{pk} retrieved."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 4: CancelOrderView
# POST /api/orders/<pk>/cancel/
# ═════════════════════════════════════════════════════════════════════════════
class CancelOrderView(APIView):
    """
    Allows the customer to cancel their own order, but ONLY if the
    order status is still 'pending' or 'confirmed'.

    Once an order is 'shipped', cancellation is no longer possible —
    the package is already on its way.

    On cancellation:
      1. Set order status to 'cancelled'
      2. Restore stock for all order items
      3. Send cancellation notification
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.prefetch_related('items__product').get(
                pk=pk,
                user=request.user
            )
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        # Enforce the cancellation rule
        cancellable_statuses = [Order.Status.PENDING, Order.Status.CONFIRMED]
        if order.status not in cancellable_statuses:
            return error_response(
                message=(
                    f"Order #{pk} cannot be cancelled because it is already '{order.status}'. "
                    f"Only pending or confirmed orders can be cancelled."
                ),
                status_code=400
            )

        with transaction.atomic():
            # Update order status
            order.status = Order.Status.CANCELLED
            order.save()

            # Update payment status if exists
            if hasattr(order, 'payment'):
                order.payment.status = Payment.PaymentStatus.REFUNDED
                order.payment.save()

            # Restore stock for each ordered item
            # F('stock') + item.quantity runs in SQL — safe for concurrent requests
            for item in order.items.all():
                if item.product:
                    from products.models import Product
                    Product.objects.filter(id=item.product_id).update(
                        stock=F('stock') + item.quantity
                    )

            # Notify the customer
            send_notification(
                user    = request.user,
                title   = "Order Cancelled",
                message = (
                    f"Your order #{order.id} has been cancelled. "
                    f"Stock has been restored. Contact support for refund queries."
                ),
                notification_type = 'order',
                link  = f"/orders/{order.id}",
            )

        serializer = OrderSerializer(order, context={'request': request})
        return success_response(
            data    = serializer.data,
            message = f"Order #{pk} cancelled successfully."
        )


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN VIEW 5: AdminOrderListView
# GET /api/orders/admin/
# ═════════════════════════════════════════════════════════════════════════════
class AdminOrderListView(APIView):
    """
    Admin-only: lists ALL orders across all users.

    Supports filtering:
      ?status=pending|confirmed|shipped|delivered|cancelled
      ?user_id=<id>  → orders from a specific customer
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        queryset = Order.objects.select_related('user').prefetch_related(
            'items', 'payment'
        ).order_by('-created_at')

        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter and status_filter in dict(Order.Status.choices):
            queryset = queryset.filter(status=status_filter)

        # Filter by specific user
        user_id = request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        paginator  = OrderPagination()
        page       = paginator.paginate_queryset(queryset, request)
        serializer = OrderSerializer(page, many=True, context={'request': request})

        return paginated_response(
            paginator = paginator,
            data      = serializer.data,
            message   = "All orders retrieved."
        )


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN VIEW 6: AdminOrderDetailView
# GET   /api/orders/admin/<pk>/ → view any order
# PATCH /api/orders/admin/<pk>/ → update order status
# ═════════════════════════════════════════════════════════════════════════════
class AdminOrderDetailView(APIView):
    """
    Admin-only: view and update any order's status.

    When the admin updates the status:
      1. Save the new status
      2. Automatically send a notification to the customer
      3. If CANCELLED → restore stock
    """
    permission_classes = [IsAdminUser]

    def _get_order(self, pk):
        try:
            return Order.objects.select_related('user').prefetch_related(
                'items__product', 'payment'
            ).get(pk=pk)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self._get_order(pk)
        if not order:
            return error_response(message="Order not found.", status_code=404)

        serializer = OrderSerializer(order, context={'request': request})
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        order = self._get_order(pk)
        if not order:
            return error_response(message="Order not found.", status_code=404)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid status update.",
                errors=serializer.errors
            )

        new_status = serializer.validated_data['status']
        old_status = order.status

        if new_status == old_status:
            return error_response(
                message=f"Order is already in '{old_status}' status.",
                status_code=400
            )

        with transaction.atomic():
            order.status = new_status
            order.save()

            # If admin cancels order — restore stock
            if new_status == Order.Status.CANCELLED and old_status != Order.Status.CANCELLED:
                for item in order.items.all():
                    if item.product:
                        from products.models import Product
                        Product.objects.filter(id=item.product_id).update(
                            stock=F('stock') + item.quantity
                        )

                # Mark payment as refunded if it was completed
                if hasattr(order, 'payment') and order.payment.status == Payment.PaymentStatus.COMPLETED:
                    order.payment.status = Payment.PaymentStatus.REFUNDED
                    order.payment.save()

            # If admin marks as delivered — mark payment as completed for COD
            if new_status == Order.Status.DELIVERED:
                if hasattr(order, 'payment'):
                    if order.payment.payment_method == Payment.Method.COD:
                        order.payment.status = Payment.PaymentStatus.COMPLETED
                        order.payment.paid_at = timezone.now()
                        order.payment.save()

            # Send notification to the customer
            if order.user and new_status in ORDER_NOTIFICATIONS:
                title, msg_template, notif_type = ORDER_NOTIFICATIONS[new_status]
                send_notification(
                    user    = order.user,
                    title   = title,
                    message = msg_template.format(id=order.id),
                    notification_type = notif_type,
                    link  = f"/orders/{order.id}",
                )

        # Return the freshly loaded order
        updated_order = Order.objects.prefetch_related(
            'items__product__images', 'items__product__category', 'payment'
        ).get(pk=pk)

        resp_serializer = OrderSerializer(updated_order, context={'request': request})
        return success_response(
            data    = resp_serializer.data,
            message = f"Order #{pk} status updated from '{old_status}' to '{new_status}'."
        )


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN VIEW 7: AdminOrderAnalyticsView
# GET /api/orders/admin/analytics/
# ═════════════════════════════════════════════════════════════════════════════
class AdminOrderAnalyticsView(APIView):
    """
    Admin-only: summary statistics for the admin dashboard.

    Returns counts and totals by status, recent orders, and revenue.
    Used by the Charts & Analytics dashboard (Phase 13).
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncDay
        from django.utils import timezone
        import datetime

        all_orders = Order.objects.all()

        # Overall counts by status
        status_counts = {
            status: all_orders.filter(status=status).count()
            for status, _ in Order.Status.choices
        }

        # Revenue from completed/delivered orders
        total_revenue = all_orders.filter(
            status__in=[Order.Status.DELIVERED, Order.Status.CONFIRMED, Order.Status.SHIPPED]
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        # Orders placed in the last 30 days grouped by day
        thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
        daily_orders = (
            all_orders
            .filter(created_at__gte=thirty_days_ago)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(count=Count('id'), revenue=Sum('total_amount'))
            .order_by('day')
        )

        # Most recent 5 orders
        recent_orders = OrderSerializer(
            all_orders.select_related('user').prefetch_related('items', 'payment').order_by('-created_at')[:5],
            many=True,
            context={'request': request}
        ).data

        return success_response(data={
            'total_orders':    all_orders.count(),
            'total_revenue':   str(total_revenue),
            'status_counts':   status_counts,
            'daily_orders':    [
                {
                    'date':    entry['day'].strftime('%Y-%m-%d'),
                    'orders':  entry['count'],
                    'revenue': str(entry['revenue'] or 0),
                }
                for entry in daily_orders
            ],
            'recent_orders':   recent_orders,
        }, message="Analytics retrieved.")
