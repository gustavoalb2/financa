from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    initial_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'), 
        verbose_name="Saldo Inicial / de Partida"
    )
    currency = models.CharField(max_length=5, default="R$", verbose_name="Moeda")

    def __str__(self):
        return f"Perfil de {self.user.username}"

    def get_total_income_all_time(self):
        total = self.user.transactions.filter(type='INCOME').aggregate(Sum('amount'))['amount__sum']
        return total or Decimal('0.00')

    def get_total_expense_all_time(self):
        total = self.user.transactions.filter(type='EXPENSE').aggregate(Sum('amount'))['amount__sum']
        return total or Decimal('0.00')

    def get_current_balance(self):
        return self.initial_balance + self.get_total_income_all_time() - self.get_total_expense_all_time()


class Category(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Receita / Entradas'),
        ('EXPENSE', 'Despesa / Saídas'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='EXPENSE', verbose_name="Tipo")
    color = models.CharField(max_length=20, default='#6366f1', verbose_name="Cor (HEX)")
    icon = models.CharField(max_length=50, default='bi-tag-fill', verbose_name="Ícone Bootstrap")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=150, verbose_name="Nome do Produto")
    sku = models.CharField(max_length=50, blank=True, null=True, verbose_name="SKU / Código")
    unit = models.CharField(max_length=20, default="un", verbose_name="Unidade de Medida")
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Preço Custo Unitário (R$)"
    )
    sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Preço Venda Unitário (R$)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.unit})"

    def get_current_stock(self):
        # Calculate stock based on linked transactions where affects_stock=True
        # EXPENSE (Compra de produto) -> adiciona no estoque
        # INCOME (Venda de produto) -> subtrai do estoque
        entries = self.transactions.filter(affects_stock=True, type='EXPENSE').aggregate(Sum('quantity'))['quantity__sum'] or Decimal('0.00')
        exits = self.transactions.filter(affects_stock=True, type='INCOME').aggregate(Sum('quantity'))['quantity__sum'] or Decimal('0.00')
        return entries - exits


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Receita / Entradas'),
        ('EXPENSE', 'Despesa / Saídas'),
    ]

    PAYMENT_METHODS = [
        ('PIX', 'Pix'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('DINHEIRO', 'Dinheiro'),
        ('TRANSFERENCIA', 'Transferência'),
        ('OUTRO', 'Outro'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="Tipo")
    description = models.CharField(max_length=255, verbose_name="Descrição")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor (R$)")
    date = models.DateField(verbose_name="Data")
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='transactions',
        verbose_name="Categoria"
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHODS, 
        default='PIX', 
        verbose_name="Forma de Pagamento"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    # Stock Integration
    affects_stock = models.BooleanField(default=False, verbose_name="Afeta Estoque?")
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="Produto"
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Quantidade"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} - R$ {self.amount} ({self.date.strftime('%d/%m/%Y')})"

