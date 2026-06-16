from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """
    Grants access only to users where is_admin=True OR is_staff=True.

    We use our own is_admin field (set on our custom User model) rather than
    Django's built-in is_staff, because:
      - is_staff grants access to the Django admin panel
      - is_admin grants access to our CUSTOM React admin dashboard
    These are intentionally separate — a support agent might access our
    dashboard without having full Django admin panel access.

    Usage in a view:
        permission_classes = [IsAdminUser]
    """
    message = "Access restricted to administrators only."

    def has_permission(self, request, view):
        # request.user is the User object for the logged-in user.
        # is_authenticated confirms a valid JWT was sent.
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_staff)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allows access if the request user owns the object,
    OR if the user is an admin.

    "Object-level" means this runs on a specific row, not the whole table.
    DRF calls has_object_permission() after has_permission() passes.

    For this to work, your model must have a 'user' field (FK to User).

    Usage in a view:
        permission_classes = [IsOwnerOrAdmin]
        # Then in the view, call: self.check_object_permissions(request, obj)
    """
    message = "You do not have permission to access this resource."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins can access anything
        if request.user.is_admin or request.user.is_staff:
            return True

        # The object must have a 'user' field linking it to its owner.
        # e.g. Cart.user, Order.user, Wishlist.user
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # If the object IS a user (e.g., profile endpoint), check identity directly.
        return obj == request.user


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allows unauthenticated users to read (GET, HEAD, OPTIONS) but
    requires authentication for write operations (POST, PUT, PATCH, DELETE).

    Used for endpoints like product list/detail:
      - Anyone can browse products (no login needed)
      - Only logged-in users can add to cart or write reviews

    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') — defined by DRF.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
