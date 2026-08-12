import os
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from financas.models import Category, UserProfile


DEFAULT_CATEGORIES = [
    {'name': 'Salário', 'type': 'INCOME', 'color': '#10b981', 'icon': 'bi-briefcase-fill'},
    {'name': 'Freelance / Serviços', 'type': 'INCOME', 'color': '#06b6d4', 'icon': 'bi-laptop-fill'},
    {'name': 'Investimentos', 'type': 'INCOME', 'color': '#3b82f6', 'icon': 'bi-graph-up-arrow'},
    {'name': 'Vendas / Rendimentos', 'type': 'INCOME', 'color': '#8b5cf6', 'icon': 'bi-cash-coin'},
    {'name': 'Outras Receitas', 'type': 'INCOME', 'color': '#14b8a6', 'icon': 'bi-piggy-bank-fill'},
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
    help = 'Inicializa categorias, perfis e o superusuário do ambiente.'

    def handle(self, *args, **options):
        for category in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(
                name=category['name'],
                type=category['type'],
                defaults={
                    'color': category['color'],
                    'icon': category['icon'],
                    'is_default': True,
                },
            )

        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@financas.local')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
        admin = User.objects.filter(username=username).first()

        if admin is None and not User.objects.filter(is_superuser=True).exists():
            if not password:
                raise CommandError(
                    'Defina DJANGO_SUPERUSER_PASSWORD para criar o superusuário automaticamente.'
                )
            admin = User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Superusuário criado: {username}'))
        elif admin is not None and not admin.is_superuser:
            admin.is_staff = True
            admin.is_superuser = True
            admin.save(update_fields=['is_staff', 'is_superuser'])
            self.stdout.write(self.style.SUCCESS(f'Usuário promovido a superusuário: {username}'))
        else:
            self.stdout.write(self.style.SUCCESS('Superusuário já existente.'))

        for user in User.objects.all():
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'initial_balance': Decimal('0.00')},
            )
        self.stdout.write(self.style.SUCCESS('Perfis de usuário verificados.'))
