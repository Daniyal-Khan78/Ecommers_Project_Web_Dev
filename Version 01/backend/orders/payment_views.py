import stripe
import json
import logging

from django.conf import settings as django_settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Order, Payment
from .serializers import OrderSerializer
from utils.responses import success_response, error_response
from utils.permissions import IsAdminUser
from utils.notifications import send_notification

# Set the Stripe secret key (from settings.py)
# All stripe.* calls below use this key automatically
stripe.api_key = django_settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 1: CreatePaymentIntentView
# POST /api/payments/create-intent/
# ═════════════════════════════════════════════════════════════════════════════
class CreatePaymentIntentView(APIView):
    """
    Creates a Stripe PaymentIntent for a specific order.

    A PaymentIntent represents one payment attempt. It stores:
      - The amount to charge (in the smallest currency unit — cents)
      - The currency
      - The customer's metadata
      - Its lifecycle status (requires_payment_method → processing → succeeded)

    What we return to React:
      - client_secret: a temporary token React passes to Stripe.js
        to complete the payment. Stripe.js collects the card details
        and processes the payment directly with Stripe's servers.
        The card number NEVER passes through our Django server.

    Accepts Visa, Mastercard, Amex, Discover, UnionPay, and more —
    Stripe handles all of them with the same 'card' payment method type.

    Request body:
        { "order_id": 1 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')

        if not order_id:
            return error_response(
                message="order_id is required.",
                status_code=400
            )

        # Verify this order belongs to the requesting user
        try:
            order = Order.objects.select_related('user').prefetch_related(
                'payment'
            ).get(pk=order_id, user=request.user)
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        # Cannot pay for cancelled or already-delivered orders
        if order.status in [Order.Status.CANCELLED, Order.Status.DELIVERED]:
            return error_response(
                message=f"Cannot process payment for an order with status '{order.status}'.",
                status_code=400
            )

        # Check if payment already completed
        if hasattr(order, 'payment') and order.payment.status == Payment.PaymentStatus.COMPLETED:
            return error_response(
                message="This order has already been paid.",
                status_code=400
            )

        try:
            # Convert order total to smallest currency unit (cents/paisa).
            # Stripe requires integers: $29.99 → 2999 cents
            # We multiply by 100 and convert to int.
            amount_cents = int(order.total_amount * 100)

            # Create the PaymentIntent with Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount   = amount_cents,
                currency = 'usd',   # Change to 'pkr' for Pakistani Rupees if Stripe supports it in your region

                # payment_method_types=['card'] enables ALL card brands:
                # Visa, Mastercard, American Express, Discover, Diners, JCB, UnionPay
                payment_method_types = ['card'],

                # Metadata is stored on Stripe's dashboard — useful for support queries
                metadata = {
                    'order_id':   order.id,
                    'user_email': request.user.email,
                    'user_id':    request.user.id,
                },

                # Description shown on Stripe dashboard and customer receipts
                description = f"ShopNest Order #{order.id} for {request.user.email}",

                # Automatically send a receipt email via Stripe (optional)
                receipt_email = request.user.email,
            )

            # Store the PaymentIntent ID on our Payment record
            # so we can look it up later when Stripe sends the webhook
            payment, _ = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'payment_method':        Payment.Method.STRIPE,
                    'amount':                order.total_amount,
                    'status':                Payment.PaymentStatus.PENDING,
                    'stripe_payment_intent': payment_intent.id,
                }
            )

            # Update the payment intent ID if the record already existed
            if payment.stripe_payment_intent != payment_intent.id:
                payment.stripe_payment_intent = payment_intent.id
                payment.save()

            return success_response(
                data={
                    # React passes this to stripe.confirmCardPayment()
                    'client_secret':      payment_intent.client_secret,

                    # The PaymentIntent ID (used in /confirm/)
                    'payment_intent_id':  payment_intent.id,

                    # The publishable key — React needs it to initialize Stripe.js
                    # We send it here so React doesn't need it hardcoded
                    'publishable_key':    django_settings.STRIPE_PUBLISHABLE_KEY,

                    # Useful metadata for the frontend to display
                    'amount':             str(order.total_amount),
                    'currency':           'usd',
                    'order_id':           order.id,

                    # Tell the frontend which card networks are accepted
                    'accepted_cards':     ['Visa', 'Mastercard', 'Amex', 'Discover', 'UnionPay'],
                },
                message="Payment session created. Complete your payment."
            )

        except stripe.error.AuthenticationError:
            logger.error("Stripe authentication failed — check STRIPE_SECRET_KEY in settings.py")
            return error_response(
                message="Payment service configuration error. Please contact support.",
                status_code=500
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return error_response(
                message=f"Payment service error: {str(e)}",
                status_code=400
            )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 2: ConfirmPaymentView
# POST /api/payments/confirm/
# ═════════════════════════════════════════════════════════════════════════════
class ConfirmPaymentView(APIView):
    """
    Called by React after Stripe has processed the card payment on the frontend.

    Stripe.js (running in the browser) handles:
      - Collecting Visa/Mastercard/Amex card details securely
      - Sending card data directly to Stripe (never to our server)
      - Returning a payment_intent_id when the card is charged

    React then calls this endpoint to tell our backend:
      "Stripe confirmed the payment — please update the order."

    We verify with Stripe (don't just trust the frontend) before
    marking the order as paid. Never trust client-side claims.

    Request body:
        { "order_id": 1, "payment_intent_id": "pi_3abc123..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id          = request.data.get('order_id')
        payment_intent_id = request.data.get('payment_intent_id')

        if not order_id or not payment_intent_id:
            return error_response(
                message="Both order_id and payment_intent_id are required.",
                status_code=400
            )

        # Get the order (must belong to this user)
        try:
            order = Order.objects.prefetch_related('payment').get(
                pk=order_id,
                user=request.user
            )
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        try:
            # Retrieve the PaymentIntent from Stripe to verify its status.
            # We NEVER trust what the client sends — we verify with Stripe directly.
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        except stripe.error.StripeError as e:
            return error_response(
                message=f"Could not verify payment with Stripe: {str(e)}",
                status_code=400
            )

        # Check the PaymentIntent status returned by Stripe
        # 'succeeded' = Visa/Mastercard/Amex charge was successful
        if payment_intent.status == 'succeeded':
            # Update our Payment record
            payment = order.payment
            payment.status               = Payment.PaymentStatus.COMPLETED
            payment.stripe_payment_id    = payment_intent.id
            payment.stripe_payment_intent = payment_intent_id
            payment.paid_at              = timezone.now()
            payment.save()

            # Upgrade order status from pending to confirmed
            if order.status == Order.Status.PENDING:
                order.status = Order.Status.CONFIRMED
                order.save()

            # Notify customer
            send_notification(
                user    = request.user,
                title   = "Payment Successful!",
                message = (
                    f"Your payment of ${order.total_amount} for Order #{order.id} "
                    f"was successful. Your order is now confirmed!"
                ),
                notification_type = 'payment',
                link  = f"/orders/{order.id}",
            )

            # Return the updated order
            order_serializer = OrderSerializer(
                Order.objects.prefetch_related(
                    'items__product__images',
                    'items__product__category',
                    'payment'
                ).get(pk=order.pk),
                context={'request': request}
            )
            return success_response(
                data    = order_serializer.data,
                message = f"Payment confirmed! Order #{order.id} is now being processed."
            )

        elif payment_intent.status == 'requires_action':
            # This happens with 3D Secure cards (Visa Secure / Mastercard ID Check)
            # The customer must complete an extra authentication step
            return error_response(
                message="Additional authentication required (3D Secure). Please complete the verification in the payment form.",
                errors={"requires_action": True, "client_secret": payment_intent.client_secret},
                status_code=402
            )

        elif payment_intent.status == 'requires_payment_method':
            # Card was declined
            return error_response(
                message="Your card was declined. Please try a different card.",
                errors={"stripe_status": payment_intent.status},
                status_code=400
            )

        else:
            return error_response(
                message=f"Unexpected payment status: '{payment_intent.status}'. Please contact support.",
                errors={"stripe_status": payment_intent.status},
                status_code=400
            )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 3: StripeWebhookView
# POST /api/payments/webhook/
# ═════════════════════════════════════════════════════════════════════════════
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Handles webhook events sent automatically by Stripe.

    Why webhooks?
      The /confirm/ endpoint above works when React explicitly calls it.
      But what if the user's browser crashes after payment but before calling /confirm/?
      The customer's Visa/Mastercard was charged but our order shows 'pending'.

      Stripe solves this by sending a POST request to our webhook URL
      directly (not through the browser) whenever a payment succeeds.
      This is a reliable BACKUP that works even if the frontend fails.

    Security:
      Stripe signs every webhook request with STRIPE_WEBHOOK_SECRET.
      We verify this signature before trusting the event.
      Without this check, anyone could send fake payment events to your server.

    CSRF:
      We exempt this view from CSRF because Stripe cannot send CSRF tokens.
      This is safe because we verify the Stripe signature instead.

    Stripe CLI for local testing:
      stripe listen --forward-to http://localhost:8000/api/payments/webhook/
    """
    permission_classes = [AllowAny]  # Stripe sends no JWT — auth is via signature

    def post(self, request):
        payload   = request.body         # Raw bytes — must NOT be parsed before verification
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        webhook_secret = django_settings.STRIPE_WEBHOOK_SECRET

        # If webhook secret is not configured, skip verification (development only)
        if not webhook_secret or webhook_secret == 'whsec_your_webhook_secret_here':
            logger.warning("Stripe webhook secret not configured — skipping signature verification (dev only)")
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                return error_response(message="Invalid payload.", status_code=400)
        else:
            # Production: verify the webhook signature
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except ValueError:
                # Invalid payload — not valid JSON
                return error_response(message="Invalid webhook payload.", status_code=400)
            except stripe.error.SignatureVerificationError:
                # Signature doesn't match — possible spoofing attempt
                logger.warning("Stripe webhook signature verification FAILED")
                return error_response(message="Webhook signature verification failed.", status_code=400)

        # Route to the appropriate handler based on event type
        event_type = event.get('type') if isinstance(event, dict) else event.type

        handlers = {
            'payment_intent.succeeded':              self._handle_payment_succeeded,
            'payment_intent.payment_failed':         self._handle_payment_failed,
            'payment_intent.canceled':               self._handle_payment_canceled,
            'charge.dispute.created':                self._handle_dispute,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event)

        # Always return 200 to Stripe, even for unhandled events.
        # If we return 4xx/5xx, Stripe will retry the webhook up to 3 days.
        from django.http import JsonResponse
        return JsonResponse({"received": True}, status=200)

    def _handle_payment_succeeded(self, event):
        """
        Fired when Stripe confirms a Visa/Mastercard/Amex payment succeeded.
        This is the backup for when the frontend fails to call /confirm/.
        """
        if isinstance(event, dict):
            intent = event['data']['object']
            intent_id = intent['id']
            metadata  = intent.get('metadata', {})
        else:
            intent    = event.data.object
            intent_id = intent.id
            metadata  = intent.metadata

        order_id = metadata.get('order_id')
        if not order_id:
            return

        try:
            payment = Payment.objects.select_related('order__user').get(
                stripe_payment_intent=intent_id
            )
        except Payment.DoesNotExist:
            logger.warning(f"Webhook: Payment not found for intent {intent_id}")
            return

        # Only update if not already completed (idempotent)
        if payment.status != Payment.PaymentStatus.COMPLETED:
            payment.status    = Payment.PaymentStatus.COMPLETED
            payment.paid_at   = timezone.now()
            payment.save()

            order = payment.order
            if order.status == Order.Status.PENDING:
                order.status = Order.Status.CONFIRMED
                order.save()

            if order.user:
                send_notification(
                    user    = order.user,
                    title   = "Payment Received!",
                    message = f"Your payment for Order #{order.id} has been received.",
                    notification_type = 'payment',
                    link  = f"/orders/{order.id}",
                )
            logger.info(f"Webhook: Payment for Order #{order_id} confirmed via webhook.")

    def _handle_payment_failed(self, event):
        """Card was declined — Visa/Mastercard/Amex all send this event on failure."""
        if isinstance(event, dict):
            intent    = event['data']['object']
            intent_id = intent['id']
        else:
            intent    = event.data.object
            intent_id = intent.id

        try:
            payment = Payment.objects.select_related('order__user').get(
                stripe_payment_intent=intent_id
            )
            payment.status = Payment.PaymentStatus.FAILED
            payment.save()

            if payment.order.user:
                send_notification(
                    user    = payment.order.user,
                    title   = "Payment Failed",
                    message = f"Payment for Order #{payment.order.id} failed. Please try again with a different card.",
                    notification_type = 'payment',
                    link  = f"/orders/{payment.order.id}",
                )
        except Payment.DoesNotExist:
            pass

    def _handle_payment_canceled(self, event):
        """PaymentIntent was cancelled (e.g., customer took too long)."""
        if isinstance(event, dict):
            intent_id = event['data']['object']['id']
        else:
            intent_id = event.data.object.id

        Payment.objects.filter(
            stripe_payment_intent=intent_id
        ).update(status=Payment.PaymentStatus.FAILED)

    def _handle_dispute(self, event):
        """A customer disputed a Visa/Mastercard charge (chargeback)."""
        logger.warning(f"Stripe dispute created: {event}")
        # In production: notify admin team immediately


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 4: PaymentStatusView
# GET /api/payments/order/<order_id>/
# ═════════════════════════════════════════════════════════════════════════════
class PaymentStatusView(APIView):
    """
    Returns the current payment status for a specific order.
    Used by React to poll payment status after redirect from 3D Secure.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related('payment').get(
                pk=order_id,
                user=request.user
            )
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        if not hasattr(order, 'payment'):
            return success_response(data={
                'order_id':       order.id,
                'order_status':   order.status,
                'payment_status': None,
                'message':        "No payment initiated yet.",
            })

        payment = order.payment
        return success_response(data={
            'order_id':           order.id,
            'order_status':       order.status,
            'payment_status':     payment.status,
            'payment_method':     payment.payment_method,
            'amount':             str(payment.amount),
            'paid_at':            payment.paid_at,
            'stripe_payment_id':  payment.stripe_payment_id,
        })


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 5: AdminRefundView
# POST /api/payments/admin/refund/
# ═════════════════════════════════════════════════════════════════════════════
class AdminRefundView(APIView):
    """
    Admin-only: issue a full or partial refund for a Stripe payment.
    Refunds go back to the original Visa/Mastercard/Amex card automatically.

    Request body:
        { "order_id": 1, "amount": 29.99 }   (amount optional — omit for full refund)
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return error_response(message="order_id is required.", status_code=400)

        try:
            payment = Payment.objects.select_related('order').get(order_id=order_id)
        except Payment.DoesNotExist:
            return error_response(message="Payment not found for this order.", status_code=404)

        if payment.status != Payment.PaymentStatus.COMPLETED:
            return error_response(
                message=f"Cannot refund a payment with status '{payment.status}'.",
                status_code=400
            )

        if not payment.stripe_payment_id:
            return error_response(
                message="No Stripe charge ID found. This may be a Cash on Delivery order.",
                status_code=400
            )

        # Refund amount (in cents). If not specified, refund the full amount.
        refund_amount = request.data.get('amount')
        refund_cents  = int(float(refund_amount) * 100) if refund_amount else None

        try:
            refund_params = {'payment_intent': payment.stripe_payment_id}
            if refund_cents:
                refund_params['amount'] = refund_cents

            refund = stripe.Refund.create(**refund_params)

        except stripe.error.StripeError as e:
            return error_response(
                message=f"Refund failed: {str(e)}",
                status_code=400
            )

        # Update payment status
        payment.status = Payment.PaymentStatus.REFUNDED
        payment.save()

        # Update order status
        payment.order.status = Order.Status.CANCELLED
        payment.order.save()

        # Notify customer
        if payment.order.user:
            refunded_amount = refund_amount or payment.amount
            send_notification(
                user    = payment.order.user,
                title   = "Refund Issued",
                message = (
                    f"A refund of ${refunded_amount} for Order #{payment.order.id} "
                    f"has been issued to your original Visa/Mastercard/card. "
                    f"It may take 5-10 business days to appear."
                ),
                notification_type = 'payment',
                link  = f"/orders/{payment.order.id}",
            )

        return success_response(
            data={
                'refund_id':     refund.id,
                'amount':        str(refund.amount / 100),
                'status':        refund.status,
            },
            message="Refund processed successfully."
        )
