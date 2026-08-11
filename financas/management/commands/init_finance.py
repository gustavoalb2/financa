from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from financas.models import UserProfile, Category
from decimal import Decimal

DEFAULT_CATEGORIES = [
    # Receitas
    {'name': 'Salário', 'type': 'INCOME', 'color': '#10b981', 'icon': 'bi-briefcase-fill'},
    {'name': 'Freelance / Serviços', 'type': 'INCOME', 'color': '#06b6d4', 'icon': 'bi-laptop-fill'},
    {'name': 'Investimentos', 'type': 'INCOME', 'color': '#3b82f6', 'icon': 'bi-graph-up-arrow'},
    {'name': 'Vendas / Rendimentos', 'type': 'INCOME', 'color': '#8b5cf6', 'icon': 'bi-cash-coin'},
    {'name': 'Outras Receitas', 'type': 'INCOME', 'color': '#14b8a6', 'icon': 'bi-piggy-bank-fill'},

    # Despesas
    {'name': 'Alimentação & Mercado', 'type': 'EXPENSE', 'color': '#ef4444', 'icon': 'bi-cart-fill'},
    {'name': 'Moradia & Aluguel', 'type': 'EXPENSE', 'color': '#f97316', 'icon': 'bi-house-door-fill'},
    {'name': 'Transporte & Combustível', 'type': 'EXPENSE', 'color': '#eab308', 'icon': 'bi-fuel-pump-fill'},
    {'name': 'Lazer & Viagens', 'type': 'EXPENSE', 'color': '#ec4899', 'icon': 'bi-controller'},
    {'name': 'Saúde & Farmácia', 'type': 'EXPENSE', 'color': '#06b6d4', 'icon': 'bi-heart-pulse-fill'},
    {'name': 'Educação & Cursos', 'type': 'EXPENSE', 'color': '#6366f1', 'icon': 'bi-book-fill'},
    {'name': 'Contas & Boletos', 'type': 'EXPENSE', 'color': '#f43f5e', 'icon': 'bi-receipt'},
    {'name': 'Compras Pessoais', 'type': 'EXPENSE', 'color': '#a855f7', 'icon': 'bi-bag-check-fill'},
    {'name': 'Outras Despesas', 'type': 'EXPENSE', 'color': '#64748b', 'icon': 'bi-three-dots'},
]


class Command(BaseCommand):
    help = 'Inicializa o banco de dados com usuário único e categorias padrão.'

    def handle(self, *args, **options):
        # 1. Seed Categories
        count_cat = 0
        for cat in DEFAULT_CATEGORIES:
            obj, created = Category.objects.get_or_create(
                name=cat['name'],
                type=cat['type'],
                defaults={
                    'color': cat['color'],
                    'icon': cat['icon'],
                    'is_default': True
                }
            )
            if created:
                count_cat += 1

        self.stdout.write(self.style.SUCCESS(f'{count_cat} categorias padrão verificadas/criadas.'))

        # 2. Check if single user exists, if not create default user
        if not User.objects.exists():
            user = User.objects.create_superuser('admin', 'admin@financas.local', 'admin123')
            UserProfile.objects.get_or_create(user=user, defaults={'initial_balance': Decimal('0.00')})
            self.stdout.write(self.style.SUCCESS('Usuário padrão criado com sucesso! Login: admin / Senha: admin123'))
        else:
            for u in User.objects.all():
                UserProfile.objects.get_or_create(user=u, defaults={'initial_balance': Decimal('0.00')})
            self.stdout.write(self.style.SUCCESS('Perfis de usuário verificados.'))
