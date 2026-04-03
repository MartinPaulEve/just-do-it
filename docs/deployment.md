# Deployment Guide

JDI runs as a Docker stack behind a Pangolin reverse proxy. Docker images are built by GitHub Actions on merge to main and pushed to a private AWS ECR repository. Updating the production server is a matter of `docker compose pull`.

## Architecture

```
Internet → Pangolin (SSL + auth) → 127.0.0.1:8000 → Daphne + WhiteNoise → Django
```

- **Pangolin** handles SSL termination and authentication
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

Save this as `trust.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::747101050174:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:MartinPaulEve/just-do-it:*"
        }
      }
    }
  ]
}
```

Then create the role and attach the ECR push policy:

```bash
aws iam create-role \
  --role-name jdi-github-ecr-push \
  --assume-role-policy-document file://trust.json

aws iam attach-role-policy \
  --role-name jdi-github-ecr-push \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
```

### 3. Add GitHub Secret

Go to the repository Settings > Secrets and variables > Actions > New repository secret:

- **Name:** `AWS_ROLE_ARN`
- **Value:** The ARN of the role created above (e.g. `arn:aws:iam::747101050174:role/jdi-github-ecr-push`)

## One-Time Server Setup

### 1. Create the Environment File

Copy `.env.prod.example` to `.env.prod` and fill in real values:

```bash
DJANGO_ENV=production
SECRET_KEY=<see below>
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
POSTGRES_DB=todo
POSTGRES_USER=todo
POSTGRES_PASSWORD=<strong password>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

Generate a secret key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2. Log In to ECR

```bash
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin \
    747101050174.dkr.ecr.us-east-1.amazonaws.com
```

Note: ECR login tokens expire after 12 hours. For unattended pulls, set up a cron job to refresh the token or use the [ECR credential helper](https://github.com/awslabs/amazon-ecr-credential-helper).

### 3. Pull and Start

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### 4. Configure Pangolin

Point Pangolin to `127.0.0.1:8000` (HTTP, not HTTPS — Pangolin handles SSL).

## Updating

After merging new code to `main`, GitHub Actions builds and pushes a new image to ECR. On the server:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

This pulls the new `latest` image and restarts the Django container. Postgres and Valkey are unaffected. Migrations run automatically on container startup via the entrypoint script.

## Recurring Tasks

A management command generates future instances of recurring tasks. Run it daily via cron on the server:

```bash
crontab -e
```

Add:

```
0 2 * * * cd /path/to/project && docker compose -f docker-compose.prod.yml exec django uv run python manage.py generate_recurring_tasks
```

This generates task instances for the next 90 days. The views also call `ensure_series_generated()` on demand, so this is a safety net rather than a hard requirement.

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
