#!/usr/bin/env bash
# Script para configurar o Neon DB localmente

echo "=================================="
echo "Configuração do Neon DB para Vercel"
echo "=================================="
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "📋 Criando .env a partir de .env.example..."
    cp .env.example .env
    echo "✅ Arquivo .env criado!"
    echo ""
    echo "⚠️  IMPORTANTE: Edite o arquivo .env com suas variáveis específicas!"
    echo ""
fi

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt
echo "✅ Dependências instaladas!"
echo ""

# Executar migrations
echo "🗄️  Executando migrations..."
python manage.py migrate
echo "✅ Migrations executadas!"
echo ""

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput
echo "✅ Arquivos estáticos coletados!"
echo ""

# Solicitar criação de superuser
read -p "Deseja criar um superuser? (s/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "=================================="
echo "✅ Configuração concluída!"
echo "=================================="
echo ""
echo "🚀 Para iniciar o servidor de desenvolvimento:"
echo "   python manage.py runserver"
echo ""
echo "📝 Próximos passos:"
echo "   1. Teste localmente"
echo "   2. Faça commit: git add . && git commit -m 'Setup Neon DB'"
echo "   3. Faça push: git push"
echo "   4. Configure as variáveis de ambiente no Vercel"
echo ""
