from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date
from financas.models import UserProfile, Category, Transaction, Product
from financas.forms import TransactionForm


class FinanceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.profile = UserProfile.objects.create(user=self.user, initial_balance=Decimal('1000.00'))
        
        self.cat_income = Category.objects.create(name='Vendas Produtos', type='INCOME', user=self.user)
        self.cat_expense = Category.objects.create(name='Produtos', type='EXPENSE', user=self.user)

        self.client = Client()

    def test_current_balance_calculation(self):
        # Initial balance: 1000.00
        self.assertEqual(self.profile.get_current_balance(), Decimal('1000.00'))

        # Add Income +500
        Transaction.objects.create(
            user=self.user,
            type='INCOME',
            description='Bonus',
            amount=Decimal('500.00'),
            date=date.today(),
            category=self.cat_income
        )

        # Add Expense -200
        Transaction.objects.create(
            user=self.user,
            type='EXPENSE',
            description='Almoço',
            amount=Decimal('200.00'),
            date=date.today(),
            category=self.cat_expense
        )

        # Recalculated balance: 1000 + 500 - 200 = 1300.00
        self.assertEqual(self.profile.get_current_balance(), Decimal('1300.00'))

    def test_dashboard_login_required(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302) # Redirect to login

    def test_dashboard_view_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, '1000,00')

    def test_transaction_create(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('transaction_create'), {
            'type': 'EXPENSE',
            'description': 'Supermercado Teste',
            'amount': '150.00',
            'date': '2026-08-01',
            'category': self.cat_expense.id,
            'payment_method': 'PIX'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.filter(user=self.user, description='Supermercado Teste').count(), 1)

    def test_stock_calculation_and_integration(self):
        self.client.login(username='testuser', password='password123')

        # 1. Create product
        prod = Product.objects.create(
            user=self.user,
            name='Camiseta Algodão',
            sku='CAM-01',
            unit='un',
            cost_price=Decimal('25.00'),
            sale_price=Decimal('50.00')
        )
        self.assertEqual(prod.get_current_stock(), Decimal('0.00'))

        # 2. Add Expense transaction (Purchase of 10 items) with affects_stock=True
        t_buy = Transaction.objects.create(
            user=self.user,
            type='EXPENSE',
            description='Compra Lote Camisetas',
            amount=Decimal('250.00'),
            date=date(2026, 8, 5),
            category=self.cat_expense,
            affects_stock=True,
            product=prod,
            quantity=Decimal('10.00')
        )
        self.assertEqual(prod.get_current_stock(), Decimal('10.00'))

        # 3. Add Income transaction (Sale of 3 items) with affects_stock=True
        t_sell = Transaction.objects.create(
            user=self.user,
            type='INCOME',
            description='Venda 3 Camisetas',
            amount=Decimal('150.00'),
            date=date(2026, 8, 8),
            category=self.cat_income,
            affects_stock=True,
            product=prod,
            quantity=Decimal('3.00')
        )
        self.assertEqual(prod.get_current_stock(), Decimal('7.00'))

        # 4. Check stock page view
        response = self.client.get(reverse('stock'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Camiseta Algodão')
        self.assertContains(response, '7,00 un')

    def test_date_persistence_in_transaction_edit_form(self):
        t = Transaction.objects.create(
            user=self.user,
            type='EXPENSE',
            description='Teste Data',
            amount=Decimal('100.00'),
            date=date(2026, 7, 15),
            category=self.cat_expense
        )
        form = TransactionForm(instance=t, user=self.user)
        self.assertEqual(form.initial['date'], '2026-07-15')

    def test_product_edit(self):
        self.client.login(username='testuser', password='password123')
        prod = Product.objects.create(
            user=self.user,
            name='Produto Antigo',
            unit='un',
            cost_price=Decimal('10.00'),
            sale_price=Decimal('20.00')
        )
        response = self.client.post(reverse('product_edit', kwargs={'pk': prod.id}), {
            'name': 'Produto Editado',
            'sku': 'PROD-NEW',
            'unit': 'kg',
            'cost_price': '15.00',
            'sale_price': '30.00'
        })
        self.assertEqual(response.status_code, 302)
        prod.refresh_from_db()
        self.assertEqual(prod.name, 'Produto Editado')
        self.assertEqual(prod.unit, 'kg')
        self.assertEqual(prod.sale_price, Decimal('30.00'))

    def test_quick_category_create_ajax(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('category_create'), {
            'name': 'Nova Categoria Rápida',
            'type': 'EXPENSE',
            'color': '#ff0000',
            'icon': 'bi-box',
            'ajax': 'true'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['name'], 'Nova Categoria Rápida')
        self.assertTrue(Category.objects.filter(name='Nova Categoria Rápida', user=self.user).exists())

    def test_quick_product_create_ajax(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('product_create'), {
            'name': 'Novo Produto Rápido',
            'sku': 'PROD-FAST',
            'unit': 'un',
            'cost_price': '10.00',
            'sale_price': '25.00',
            'ajax': 'true'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['name'], 'Novo Produto Rápido')
        self.assertTrue(Product.objects.filter(name='Novo Produto Rápido', user=self.user).exists())



