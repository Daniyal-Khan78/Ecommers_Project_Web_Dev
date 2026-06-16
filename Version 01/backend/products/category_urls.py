from django.urls import path
from .views import CategoryListCreateView, CategoryDetailView

# All URLs are prefixed with /api/categories/ (set in backend/urls.py)
urlpatterns = [
    # List all categories (public) / Create category (admin)
    path('', CategoryListCreateView.as_view(), name='category_list_create'),

    # Category detail / update / delete
    path('<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
]
