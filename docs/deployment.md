# Deployment Guide

This project runs as a Docker stack behind a reverse proxy. Docker images are built by GitHub Actions on merge to main and pushed to a container registry. Updating the production server is a matter of `docker compose pull`.

## Architecture

```
Internet → Reverse Proxy (SSL) → 127.0.0.1:8000 → Daphne + WhiteNoise → Django
```

- **Reverse proxy** handles SSL termination (e.g. Pangolin, Caddy, nginx)
- **Daphne** is the ASGI application server
- **WhiteNoise** serves static files directly from the Django process
- **PostgreSQL** and **Valkey** run as Docker containers alongside Django

## One-Time AWS Setup

The GitHub Actions workflow uses OIDC to authenticate with AWS (no long-lived credentials).

### 1. Create GitHub OIDC Provider

If you haven't already set up GitHub OIDC in your AWS account:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. Create IAM Role

Save this as `trust.json` (update the repo path):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:*"
        }
      }
    }
  ]
}
```

Then create the role and attach policies for ECR Public push:

```bash
aws iam create-role \
  --role-name project-github-ecr-push \
  --assume-role-policy-document file://trust.json

# ECR Public requires these permissions
aws iam put-role-policy \
  --role-name project-github-ecr-push \
  --policy-name ecr-public-push \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ecr-public:GetAuthorizationToken",
          "ecr-public:BatchCheckLayerAvailability",
          "ecr-public:InitiateLayerUpload",
          "ecr-public:UploadLayerPart",
          "ecr-public:CompleteLayerUpload",
          "ecr-public:PutImage",
          "sts:GetServiceBearerToken"
        ],
        "Resource": "*"
      }
    ]
  }'
```

### 3. Add GitHub Secret

Go to the repository Settings > Secrets and variables > Actions > New repository secret:

- **Name:** `AWS_ROLE_ARN`
- **Value:** The ARN of the role created above

## One-Time Server Setup

### 1. Create the Environment File

Copy `.env.prod.example` to `.env.prod` and fill in real values:

```bash
DJANGO_ENV=production
SECRET_KEY=<see below>
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
POSTGRES_DB=myproject
POSTGRES_USER=myproject
POSTGRES_PASSWORD=<strong password>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

Generate a secret key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2. Pull and Start

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### 3. Configure Reverse Proxy

Point your reverse proxy to `127.0.0.1:8000` (HTTP, not HTTPS — the proxy handles SSL).

## Updating

After merging new code to `main`, GitHub Actions builds and pushes a new image. On the server:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Migrations run automatically on container startup via the entrypoint script.

## Troubleshooting

### Check logs

```bash
docker compose -f docker-compose.prod.yml logs django
docker compose -f docker-compose.prod.yml logs postgres
```

### Run a management command

```bash
docker compose -f docker-compose.prod.yml exec django uv run python manage.py <command>
```

### Access the Django shell

```bash
docker compose -f docker-compose.prod.yml exec django uv run python manage.py shell
```

### Recreate the database (destructive)

```bash
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
```

The `-v` flag removes the Postgres data volume. The entrypoint will run migrations on a fresh database.
