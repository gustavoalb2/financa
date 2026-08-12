from django import forms
from django.db import models
from django.contrib.auth.models import User
from .models import Transaction, Category, UserProfile, Product


class TransactionForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Data"
    )

    class Meta:
        model = Transaction
        fields = ['type', 'description', 'amount', 'date', 'category', 'payment_method', 'notes', 'affects_stock', 'product', 'quantity']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select', 'id': 'id_type'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Supermercado, Salário, Freelance'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações adicionais (opcional)'}),
            'affects_stock': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_affects_stock'}),
            'product': forms.Select(attrs={'class': 'form-select', 'id': 'id_product'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'id': 'id_quantity'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.date:
            self.initial['date'] = self.instance.date.strftime('%Y-%m-%d')

        if user:
            # Filter categories owned by this user or default categories
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(user=user) | models.Q(is_default=True)
            ).order_by('type', 'name')
            self.fields['product'].queryset = Product.objects.filter(user=user).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        affects_stock = cleaned_data.get('affects_stock')
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if affects_stock:
            if not product:
                self.add_error('product', 'Selecione um produto para movimentar o estoque.')
            if not quantity or quantity <= 0:
                self.add_error('quantity', 'Informe uma quantidade válida maior que zero.')
        else:
            cleaned_data['product'] = None
            cleaned_data['quantity'] = None

        # A categoria define a natureza financeira do lançamento. Isso evita
        # que uma categoria de receita seja contabilizada como despesa quando
        # o formulário/modal permanecer no valor padrão EXPENSE.
        if category:
            cleaned_data['type'] = category.type

        return cleaned_data



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'unit', 'cost_price', 'sale_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Camiseta Básica'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CAM-001'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: un, kg, cx'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type', 'color', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Alimentação, Investimentos'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: bi-cart-fill, bi-cash-stack'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['initial_balance', 'currency']
        widgets = {
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'R$'}),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
