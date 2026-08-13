from decimal import Decimal

from django.db.models import Case, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce

from .models import Category, Product, Transaction, UserProfile


def global_finance_context(request):
    """Provides categories, products and balance data to all templates via base.html."""
    if not request.user.is_authenticated:
        return {}

    profile = getattr(request, '_finance_profile', None)
    if profile is None:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        request._finance_profile = profile
    categories = Category.objects.filter(
        Q(user=request.user) | Q(is_default=True)
    ).order_by('type', 'name')
    products = Product.objects.filter(user=request.user).annotate(
        current_stock=Coalesce(
            Sum(Case(
                When(transactions__affects_stock=True, transactions__type='EXPENSE', then=F('transactions__quantity')),
                When(transactions__affects_stock=True, transactions__type='INCOME', then=-F('transactions__quantity')),
                default=Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )),
            Value(Decimal('0.00')),
        )
    ).order_by('name')

    totals = Transaction.objects.filter(user=request.user).aggregate(
        income=Coalesce(Sum('amount', filter=Q(type='INCOME')), Value(Decimal('0.00'))),
        expense=Coalesce(Sum('amount', filter=Q(type='EXPENSE')), Value(Decimal('0.00'))),
    )

    return {
        'global_categories': categories,
        'global_products': products,
        'current_balance': profile.initial_balance + totals['income'] - totals['expense'],
    }
