from django.db.models import Q
from .models import Category, UserProfile, Product


def global_finance_context(request):
    """Provides categories, products and balance data to all templates via base.html."""
    if not request.user.is_authenticated:
        return {}

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    categories = Category.objects.filter(
        Q(user=request.user) | Q(is_default=True)
    ).order_by('type', 'name')
    products = Product.objects.filter(user=request.user).order_by('name')

    return {
        'global_categories': categories,
        'global_products': products,
        'current_balance': profile.get_current_balance(),
    }

