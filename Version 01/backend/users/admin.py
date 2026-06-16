from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


# We extend Django's built-in UserAdmin to include our extra fields.
# If we just used admin.ModelAdmin, the password fields and groups
# section wouldn't appear correctly.
@admin.register(User)
class UserAdmin(BaseUserAdmin):

    # Columns shown in the list view (the table on the admin list page).
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'is_admin', 'email_verified', 'is_staff', 'date_joined']

    # Fields you can click to filter the list (right sidebar in admin).
    list_filter = ['is_admin', 'is_staff', 'is_active', 'email_verified']

    # Fields you can search by using the search box at the top.
    search_fields = ['username', 'email', 'first_name', 'last_name']

    # Default sort order in list view.
    ordering = ['-date_joined']

    # Fields displayed on the Edit User detail page.
    # We add our extra fields (phone, address, etc.) to the existing sections.
    fieldsets = BaseUserAdmin.fieldsets + (
        ('ShopNest Profile', {
            'fields': ('phone', 'address', 'profile_image', 'is_admin', 'email_verified')
        }),
    )

    # Fields shown on the Add New User page.
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('ShopNest Profile', {
            'fields': ('email', 'phone', 'address', 'is_admin')
        }),
    )
