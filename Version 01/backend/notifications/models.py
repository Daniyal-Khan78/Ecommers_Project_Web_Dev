from django.db import models
from django.conf import settings


# ─────────────────────────────────────────────────────────────
# MODEL 11: Notification
# ─────────────────────────────────────────────────────────────
class Notification(models.Model):
    """
    In-app notification messages for users.
    Examples:
      - "Your order #42 has been shipped!"
      - "Your password was changed."
      - "A product in your wishlist is now on sale!"

    The frontend polls this endpoint periodically and shows a badge
    count (unread notifications) in the navbar.
    """

    class NotificationType(models.TextChoices):
        ORDER    = 'order',    'Order Update'
        PAYMENT  = 'payment',  'Payment'
        SYSTEM   = 'system',   'System'
        PROMO    = 'promo',    'Promotion'
        WISHLIST = 'wishlist', 'Wishlist'

    # The user this notification is for.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Short headline shown in the notification bell dropdown.
    title = models.CharField(max_length=200)

    # Full notification text.
    message = models.TextField()

    # Category of notification — used to show different icons.
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )

    # False = unread (shown with a blue dot / bold text).
    # True  = user has seen it.
    is_read = models.BooleanField(default=False)

    # Optional link to navigate to when notification is clicked.
    # Example: "/orders/42" for an order update notification.
    link = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "read" if self.is_read else "unread"
        return f"[{status}] {self.title} → {self.user.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
