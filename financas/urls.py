from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Dashboard & Core
    path('', views.dashboard_view, name='dashboard'),
    path('transacoes/', views.transaction_list_view, name='transactions'),
    path('transacoes/nova/', views.transaction_create_view, name='transaction_create'),
    path('transacoes/<int:pk>/editar/', views.transaction_edit_view, name='transaction_edit'),
    path('transacoes/<int:pk>/excluir/', views.transaction_delete_view, name='transaction_delete'),

    # Categories
    path('categorias/', views.category_list_view, name='categories'),
    path('categorias/nova/', views.category_create_view, name='category_create'),
    path('categorias/<int:pk>/excluir/', views.category_delete_view, name='category_delete'),

    # Settings & Export
    path('configuracoes/', views.settings_view, name='settings'),
    path('exportar-csv/', views.export_csv_view, name='export_csv'),

    # Stock Management
    path('estoque/', views.stock_list_view, name='stock'),
    path('estoque/produto/novo/', views.product_create_view, name='product_create'),
    path('estoque/produto/<int:pk>/editar/', views.product_edit_view, name='product_edit'),
    path('estoque/produto/<int:pk>/excluir/', views.product_delete_view, name='product_delete'),
]


