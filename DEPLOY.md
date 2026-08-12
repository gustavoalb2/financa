# Deploy com GitHub, Vercel e Neon

## 1. GitHub

1. Crie um repositório no GitHub.
2. Faça o primeiro commit e push:

```bash
git add .
git commit -m "Preparar deploy com PostgreSQL"
git push -u origin main
```

O banco local `db.sqlite3` e arquivos `.env` ficam fora do Git por segurança.

## 2. Neon

1. Crie um projeto PostgreSQL no Neon.
2. Copie a connection string do branch desejado.
3. Ela será usada como `DATABASE_URL`, normalmente no formato:

```text
postgresql://usuario:senha@host/neondb?sslmode=require
```

Use uma conexão pooled do Neon para o ambiente serverless do Vercel quando ela estiver disponível.

## 3. Vercel

1. Importe o repositório do GitHub em **New Project**.
2. O Vercel detecta `manage.py` e o projeto Django automaticamente.
3. Em **Settings > Environment Variables**, adicione para **Production** e, se desejar, Preview:

```text
DJANGO_SECRET_KEY=<uma-chave-gerada-e-secreta>
DJANGO_DEBUG=False
DATABASE_URL=<connection-string-do-Neon>
DJANGO_ALLOWED_HOSTS=.vercel.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app
```

Se usar domínio próprio, acrescente o domínio sem apagar `.vercel.app`:

```text
DJANGO_ALLOWED_HOSTS=.vercel.app,app.seudominio.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://app.seudominio.com
```

Depois, faça um redeploy.

## 4. Migrações e dados iniciais

Após o primeiro deploy, execute as migrações apontando para o Neon. Com a CLI do Vercel:

```bash
vercel env pull .env.production.local
python manage.py migrate
python manage.py init_finance
```

O comando `init_finance` cria as categorias padrão e, se o banco estiver vazio, um usuário inicial. Troque a senha inicial imediatamente ou crie um superusuário próprio:

```bash
python manage.py createsuperuser
```

Não coloque valores de `DATABASE_URL` ou `DJANGO_SECRET_KEY` no GitHub.
