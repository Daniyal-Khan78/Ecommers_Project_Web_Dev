from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_cart(sender, instance, created, **kwargs):
    """
    Automatically creates a Cart for every new User.

    How signals work:
      - 'post_save'   = run AFTER a model's .save() method completes
      - 'sender'      = which model to watch (our User model)
      - 'instance'    = the actual User object that was just saved
      - 'created'     = True if this was an INSERT (new record), False for UPDATE

    We only create the cart on 'created=True' to avoid creating a new cart
    every time a user's profile is updated.

    We use a lazy import inside the function to avoid circular import errors.
    (users → cart → users would be a circular chain if imported at the top.)
    """
    if created:
        # Import here (not at top of file) to prevent circular imports.
        # users/signals.py → cart/models.py is fine.
        # But if cart/models.py imported from users, we'd have a circle.
        from cart.models import Cart
        Cart.objects.create(user=instance)
