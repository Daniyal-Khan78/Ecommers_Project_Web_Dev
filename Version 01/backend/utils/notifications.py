def send_notification(user, title, message, notification_type='system', link=''):
    """
    Creates an in-app Notification record for a user.

    Called from views whenever something important happens:
      - Order confirmed → notify customer
      - Payment received → notify customer
      - Product back in stock (wishlist) → notify customer

    Uses lazy import to avoid circular import issues.

    Usage:
        from utils.notifications import send_notification
        send_notification(
            user=order.user,
            title="Order Shipped!",
            message=f"Your order #{order.id} has been shipped.",
            notification_type='order',
            link=f"/orders/{order.id}"
        )
    """
    from notifications.models import Notification

    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
