import os
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from financas.models import Category, UserProfile


class Command(BaseCommand):
    help = 'Inicializa perfis e o superusuário do ambiente, sem categorias padrão.'

    def handle(self, *args, **options):
        # Remove apenas categorias pré-cadastradas pelo sistema. Categorias
        # criadas pelo usuário têm user preenchido e são preservadas.
        deleted, _ = Category.objects.filter(is_default=True, user__isnull=True).delete()
        if deleted:
            self.stdout.write(self.style.SUCCESS(f'{deleted} categoria(s) padrão removida(s).'))

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
