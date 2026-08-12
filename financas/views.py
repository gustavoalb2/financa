import csv
import calendar
from datetime import datetime, date
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse

from django.db.models import Case, DecimalField, F, Sum, Q, Value, When
from django.db.models.functions import Coalesce, TruncMonth
from django.core.paginator import Paginator

from .models import Transaction, Category, UserProfile, Product
from .forms import TransactionForm, CategoryForm, UserProfileForm, UserUpdateForm, ProductForm



@login_required
def dashboard_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # 1. Parse selected month and year (Default to current)
    today = date.today()
    try:
        selected_month = int(request.GET.get('month', today.month))
        selected_year = int(request.GET.get('year', today.year))
    except ValueError:
        selected_month = today.month
        selected_year = today.year

    # Validate range
    if selected_month < 1 or selected_month > 12:
        selected_month = today.month
    if selected_year < 2000 or selected_year > 2100:
        selected_year = today.year

    # Date range for selected month
    _, last_day = calendar.monthrange(selected_year, selected_month)
    period_start = date(selected_year, selected_month, 1)
    period_end = date(selected_year, selected_month, last_day)

    # 2. Query transactions for current selected period
    period_transactions = Transaction.objects.filter(
        user=user,
        date__range=[period_start, period_end]
    )

    period_totals = period_transactions.aggregate(
        income=Coalesce(Sum('amount', filter=Q(type='INCOME')), Value(Decimal('0.00'))),
        expense=Coalesce(Sum('amount', filter=Q(type='EXPENSE')), Value(Decimal('0.00'))),
    )
    incomes_period = period_totals['income']
    expenses_period = period_totals['expense']
    net_period = incomes_period - expenses_period

    # 3. Calculate percentages
    if incomes_period > Decimal('0.00'):
        expense_percentage = float((expenses_period / incomes_period) * 100)
        savings_percentage = float(((incomes_period - expenses_period) / incomes_period) * 100)
    else:
        expense_percentage = 100.0 if expenses_period > Decimal('0.00') else 0.0
        savings_percentage = 0.0

    # Clamp bounds for nice UI badges if needed
    expense_percentage = min(expense_percentage, 999.0)

    # 4. Previous month comparison
    if selected_month == 1:
        prev_month = 12
        prev_year = selected_year - 1
    else:
        prev_month = selected_month - 1
        prev_year = selected_year

    _, prev_last_day = calendar.monthrange(prev_year, prev_month)
    prev_transactions = Transaction.objects.filter(
        user=user,
        date__range=[date(prev_year, prev_month, 1), date(prev_year, prev_month, prev_last_day)]
    )
    prev_totals = prev_transactions.aggregate(
        income=Coalesce(Sum('amount', filter=Q(type='INCOME')), Value(Decimal('0.00'))),
        expense=Coalesce(Sum('amount', filter=Q(type='EXPENSE')), Value(Decimal('0.00'))),
    )
    prev_incomes = prev_totals['income']
    prev_expenses = prev_totals['expense']

    # Percentage change comparing current period vs prev period
    if prev_incomes > Decimal('0.00'):
        income_change_pct = float(((incomes_period - prev_incomes) / prev_incomes) * 100)
    else:
        income_change_pct = 100.0 if incomes_period > Decimal('0.00') else 0.0

    if prev_expenses > Decimal('0.00'):
        expense_change_pct = float(((expenses_period - prev_expenses) / prev_expenses) * 100)
    else:
        expense_change_pct = 100.0 if expenses_period > Decimal('0.00') else 0.0

    # 5. Expenses by Category (for Doughnut Chart and breakdown table)
    expenses_by_cat_qs = period_transactions.filter(type='EXPENSE').values(
        'category__name', 'category__color', 'category__icon'
    ).annotate(total=Sum('amount')).order_by('-total')

    category_breakdown = []
    cat_chart_labels = []
    cat_chart_data = []
    cat_chart_colors = []

    for item in expenses_by_cat_qs:
        cat_name = item['category__name'] or 'Sem Categoria'
        cat_color = item['category__color'] or '#64748b'
        cat_icon = item['category__icon'] or 'bi-tag-fill'
        cat_total = item['total'] or Decimal('0.00')
        cat_pct = float((cat_total / expenses_period * 100)) if expenses_period > Decimal('0.00') else 0.0

        category_breakdown.append({
            'name': cat_name,
            'color': cat_color,
            'icon': cat_icon,
            'total': cat_total,
            'percentage': round(cat_pct, 1)
        })

        cat_chart_labels.append(cat_name)
        cat_chart_data.append(float(cat_total))
        cat_chart_colors.append(cat_color)

    # 6. Monthly trend data (Last 6 Months)
    monthly_trend_labels = []
    monthly_trend_incomes = []
    monthly_trend_expenses = []

    pt_months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    trend_start_month = selected_month - 5
    trend_start_year = selected_year
    while trend_start_month <= 0:
        trend_start_month += 12
        trend_start_year -= 1
    trend_start = date(trend_start_year, trend_start_month, 1)
    trend_end = date(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
    monthly_totals = {
        row['month']: row for row in Transaction.objects.filter(
            user=user, date__range=[trend_start, trend_end]
        ).annotate(month=TruncMonth('date')).values('month').annotate(
            income=Coalesce(Sum('amount', filter=Q(type='INCOME')), Value(Decimal('0.00'))),
            expense=Coalesce(Sum('amount', filter=Q(type='EXPENSE')), Value(Decimal('0.00'))),
        )
    }

    for i in range(5, -1, -1):
        m = selected_month - i
        y = selected_year
        while m <= 0:
            m += 12
            y -= 1
        
        _, m_last = calendar.monthrange(y, m)
        month_totals = monthly_totals.get(date(y, m, 1))
        m_inc = month_totals['income'] if month_totals else Decimal('0.00')
        m_exp = month_totals['expense'] if month_totals else Decimal('0.00')

        monthly_trend_labels.append(f"{pt_months[m-1]}/{y}")
        monthly_trend_incomes.append(float(m_inc))
        monthly_trend_expenses.append(float(m_exp))

    # 7. Recent Transactions (Last 6)
    recent_transactions = Transaction.objects.filter(user=user).select_related('category')[:6]

    # Month names for dropdown selector
    months_list = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    years_list = range(today.year - 3, today.year + 4)

    context = {
        'profile': profile,
        'current_balance': profile.get_current_balance(),
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_month_name': dict(months_list).get(selected_month),
        'months_list': months_list,
        'years_list': years_list,
        
        'incomes_period': incomes_period,
        'expenses_period': expenses_period,
        'net_period': net_period,
        'expense_percentage': round(expense_percentage, 1),
        'savings_percentage': round(savings_percentage, 1),
        'income_change_pct': round(income_change_pct, 1),
        'expense_change_pct': round(expense_change_pct, 1),

        'category_breakdown': category_breakdown,
        'cat_chart_labels': cat_chart_labels,
        'cat_chart_data': cat_chart_data,
        'cat_chart_colors': cat_chart_colors,

        'trend_labels': monthly_trend_labels,
        'trend_incomes': monthly_trend_incomes,
        'trend_expenses': monthly_trend_expenses,

        'recent_transactions': recent_transactions,
    }
    return render(request, 'financas/dashboard.html', context)


@login_required
def transaction_list_view(request):
    user = request.user
    profile = UserProfile.objects.get_or_create(user=user)[0]
    
    queryset = Transaction.objects.filter(user=user).select_related('category')

    # Filters
    search_query = request.GET.get('search', '').strip()
    type_filter = request.GET.get('type', '')
    category_filter = request.GET.get('category', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if search_query:
        queryset = queryset.filter(Q(description__icontains=search_query) | Q(notes__icontains=search_query))
    if type_filter in ['INCOME', 'EXPENSE']:
        queryset = queryset.filter(type=type_filter)
    if category_filter.isdigit():
        queryset = queryset.filter(category_id=int(category_filter))
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    # Totals of current filtered query
    total_incomes = queryset.filter(type='INCOME').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_expenses = queryset.filter(type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    filtered_net = total_incomes - total_expenses

    # Pagination
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.filter(Q(user=user) | Q(is_default=True)).order_by('type', 'name')
    form = TransactionForm(user=user)

    context = {
        'profile': profile,
        'page_obj': page_obj,
        'total_incomes': total_incomes,
        'total_expenses': total_expenses,
        'filtered_net': filtered_net,
        'categories': categories,
        'form': form,
        'search_query': search_query,
        'type_filter': type_filter,
        'category_filter': category_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'financas/transactions.html', context)


@login_required
def transaction_create_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transação cadastrada com sucesso!')
            return redirect(request.POST.get('next', 'transactions'))
        else:
            messages.error(request, 'Erro ao cadastrar transação. Verifique os dados.')
    return redirect('transactions')


@login_required
def transaction_edit_view(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transação atualizada com sucesso!')
            return redirect(request.POST.get('next', 'transactions'))
        else:
            messages.error(request, 'Erro ao atualizar transação.')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    
    return render(request, 'financas/transaction_form.html', {'form': form, 'transaction': transaction})


@login_required
def transaction_delete_view(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transação excluída com sucesso!')
    return redirect(request.POST.get('next', 'transactions'))


@login_required
def category_list_view(request):
    user = request.user
    user_categories = Category.objects.filter(Q(user=user) | Q(is_default=True)).order_by('type', 'name')
    form = CategoryForm()

    context = {
        'categories': user_categories,
        'form': form,
    }
    return render(request, 'financas/categories.html', context)


@login_required
def category_create_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.user = request.user
            cat.is_default = False
            cat.save()
            if request.POST.get('ajax') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': cat.id,
                    'name': cat.name,
                    'type': cat.type,
                    'type_display': cat.get_type_display(),
                    'color': cat.color,
                    'icon': cat.icon,
                })
            messages.success(request, f'Categoria "{cat.name}" criada com sucesso!')
        else:
            if request.POST.get('ajax') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            messages.error(request, 'Erro ao criar categoria.')
    return redirect('categories')



@login_required
def category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    # Only allow deleting user's own categories or if user is superuser
    if category.user == request.user or request.user.is_superuser:
        category.delete()
        messages.success(request, 'Categoria excluída com sucesso!')
    else:
        messages.error(request, 'Você não tem permissão para excluir esta categoria padrão.')
    return redirect('categories')


@login_required
def settings_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=profile)
        user_form = UserUpdateForm(request.POST, instance=user)

        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, 'Configurações e Saldo Inicial atualizados com sucesso!')
            return redirect('settings')
        else:
            messages.error(request, 'Erro ao salvar alterações.')
    else:
        profile_form = UserProfileForm(instance=profile)
        user_form = UserUpdateForm(instance=user)

    context = {
        'profile': profile,
        'profile_form': profile_form,
        'user_form': user_form,
        'current_balance': profile.get_current_balance(),
    }
    return render(request, 'financas/settings.html', context)


@login_required
def export_csv_view(request):
    user = request.user
    queryset = Transaction.objects.filter(user=user).select_related('category').order_by('-date')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="extrato_financas_{date.today().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff'.encode('utf8')) # BOM signature for Excel in UTF-8

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Data', 'Tipo', 'Descrição', 'Valor (R$)', 'Categoria', 'Forma de Pagamento', 'Observações'])

    for t in queryset:
        cat_name = t.category.name if t.category else 'Sem Categoria'
        writer.writerow([
            t.id,
            t.date.strftime('%d/%m/%Y'),
            t.get_type_display(),
            t.description,
            f"{t.amount:.2f}".replace('.', ','),
            cat_name,
            t.get_payment_method_display(),
            t.notes or ''
        ])

    return response


@login_required
def stock_list_view(request):
    user = request.user
    products = Product.objects.filter(user=user).annotate(
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
    form = ProductForm()

    # Calculate stock data for each product
    product_list = []
    total_items_stock = Decimal('0.00')
    total_cost_value = Decimal('0.00')
    total_sale_value = Decimal('0.00')

    for p in products:
        current_stock = p.current_stock
        cost_val = current_stock * p.cost_price
        sale_val = current_stock * p.sale_price

        total_items_stock += current_stock
        total_cost_value += cost_val
        total_sale_value += sale_val

        product_list.append({
            'product': p,
            'current_stock': current_stock,
            'total_cost_val': cost_val,
            'total_sale_val': sale_val,
        })

    # Recent stock transactions
    stock_transactions = Transaction.objects.filter(
        user=user, affects_stock=True
    ).select_related('product', 'category').order_by('-date', '-created_at')[:10]

    context = {
        'product_list': product_list,
        'form': form,
        'total_products_count': products.count(),
        'total_items_stock': total_items_stock,
        'total_cost_value': total_cost_value,
        'total_sale_value': total_sale_value,
        'stock_transactions': stock_transactions,
    }
    return render(request, 'financas/stock.html', context)


@login_required
def product_create_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            if request.POST.get('ajax') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': product.id,
                    'name': product.name,
                    'unit': product.unit,
                    'cost_price': float(product.cost_price),
                    'sale_price': float(product.sale_price),
                    'current_stock': float(product.get_current_stock()),
                })
            messages.success(request, f'Produto "{product.name}" cadastrado com sucesso!')
        else:
            if request.POST.get('ajax') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            messages.error(request, 'Erro ao cadastrar produto. Verifique os dados.')
    return redirect('stock')



@login_required
def product_edit_view(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Produto "{product.name}" atualizado com sucesso!')
        else:
            messages.error(request, 'Erro ao atualizar produto. Verifique os dados.')
    return redirect('stock')


@login_required
def product_delete_view(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produto excluído com sucesso!')
    return redirect('stock')

