# Payment Gateway Integration

Sistema unificado de integração com múltiplos gateways de pagamento, oferecendo uma API consistente para processar pagamentos através de diferentes provedores.

## 🎯 **PRODUCTION READY** - Phases 1 & 2 Implementadas

✅ Autenticação JWT + RBAC  
✅ Rate Limiting  
✅ Alembic Migrations  
✅ Idempotency Keys  
✅ Sentry Error Tracking  
✅ CI/CD Pipeline  
✅ Pagamentos Recorrentes  
✅ Notificações por Email  
✅ Multi-tenancy  
✅ Testes de Integração

**[Ver documentação completa das features →](PHASE_1_2_FEATURES.md)**

---

## 🚀 Features Principais

### Core Payment Features
- **Múltiplos Gateways**: Stripe, PayPal, Mercado Pago e PagSeguro
- **Webhooks**: Sistema robusto de processamento com validação de assinaturas
- **Retry Logic**: Mecanismo automático com backoff exponencial usando Redis
- **Reporting**: Geração de relatórios detalhados sobre transações e performance
- **Logs Detalhados**: Sistema de logging estruturado com suporte a JSON

### Enterprise Features (NEW! 🆕)
- **Autenticação JWT**: Sistema completo com RBAC (Admin, User, API Client)
- **API Keys**: Gestão de chaves de API para integrações externas
- **Rate Limiting**: Proteção contra abuse (100 req/min global, customizável)
- **Idempotency**: Prevenção de duplicação de requests
- **Subscriptions**: Pagamentos recorrentes (daily, weekly, monthly, yearly)
- **Email Notifications**: Templates para todos os eventos de pagamento
- **Multi-tenancy**: Isolamento de dados por tenant
- **PCI Compliance**: Mascaramento, criptografia e boas práticas
- **Error Tracking**: Integração com Sentry
- **CI/CD**: Pipeline completo com GitHub Actions

---

## 📋 Requisitos

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

---

## 🛠 Tecnologias

### Backend
- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para PostgreSQL com Alembic migrations
- **Pydantic**: Validação de dados
- **Redis**: Cache e queue para retry logic
- **SlowAPI**: Rate limiting
- **Sentry**: Error tracking e monitoring
- **JWT**: Autenticação e autorização

### Frontend
- **React 18**: Framework UI
- **TypeScript**: Type safety
- **React Query**: Gerenciamento de estado e cache
- **Axios**: Cliente HTTP

---

## 🚀 Quick Start

### 1. Clone o repositório

```bash
git clone <repository-url>
cd payment-gateway-integration
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:
- Gateways de pagamento (Stripe, PayPal, etc)
- SMTP para emails
- Sentry DSN (opcional)
- JWT secrets

### 3. Inicie os serviços

```bash
docker-compose up -d
```

Ou use o Makefile:
```bash
make up
```

### 4. Execute as migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Crie um usuário admin

```bash
docker-compose exec backend python -c "
from app.services.auth_service import AuthService
from app.core.database import AsyncSessionLocal
from app.schemas.user import UserCreate
from app.models.user import UserRole
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        service = AuthService(db)
        await service.register_user(UserCreate(
            email='admin@example.com',
            username='admin',
            password='Admin123!@#',
            full_name='Admin User',
            role=UserRole.ADMIN
        ))
        print('Admin user created!')

asyncio.run(create_admin())
"
```

### 6. Acesse a aplicação

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

---

## 🔐 Autenticação

### Registrar e fazer login

```bash
# Registrar usuário
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "myuser",
    "password": "SecurePass123!",
    "full_name": "My User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myuser",
    "password": "SecurePass123!"
  }'
```

### Usar o token

```bash
# Salvar o token
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Usar em requests
curl http://localhost:8000/api/v1/payments/ \
  -H "Authorization: Bearer $TOKEN"
```

### Criar API Key

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Integration Key",
    "expires_days": 365
  }'
```

---

## 💳 Criar Pagamento com Idempotência

```bash
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: payment-2024-001" \
  -H "Content-Type: application/json" \
  -d '{
    "gateway": "stripe",
    "amount": 100.50,
    "currency": "USD",
    "customer_email": "customer@example.com",
    "customer_name": "John Doe",
    "description": "Product purchase"
  }'
```

---

## 📚 Documentação da API

### Principais Endpoints

#### Authentication
```
POST   /api/v1/auth/register          # Registrar usuário
POST   /api/v1/auth/login             # Login (JWT)
GET    /api/v1/auth/me                # Info do usuário
POST   /api/v1/auth/change-password   # Alterar senha
POST   /api/v1/auth/api-keys          # Criar API key
GET    /api/v1/auth/api-keys          # Listar API keys
DELETE /api/v1/auth/api-keys/{id}     # Revogar API key
```

#### Payments
```
POST   /api/v1/payments/              # Criar pagamento
GET    /api/v1/payments/              # Listar pagamentos
GET    /api/v1/payments/{id}          # Obter pagamento
POST   /api/v1/payments/{id}/sync     # Sincronizar status
POST   /api/v1/payments/refunds       # Criar reembolso
POST   /api/v1/payments/{id}/cancel   # Cancelar pagamento
```

#### Webhooks
```
POST   /api/v1/webhooks/stripe        # Webhook Stripe
POST   /api/v1/webhooks/paypal        # Webhook PayPal
POST   /api/v1/webhooks/mercadopago   # Webhook Mercado Pago
POST   /api/v1/webhooks/pagseguro     # Webhook PagSeguro
```

#### Reports
```
POST   /api/v1/reports/               # Criar relatório
GET    /api/v1/reports/               # Listar relatórios
GET    /api/v1/reports/{id}           # Obter relatório
GET    /api/v1/reports/dashboard/stats # Estatísticas
```

---

## 🧪 Testes

### Backend

```bash
# Todos os testes
docker-compose exec backend pytest

# Com coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Testes de integração
docker-compose exec backend pytest tests/test_integration.py -v

# Testes específicos
docker-compose exec backend pytest tests/test_payments.py
```

### Frontend

```bash
docker-compose exec frontend npm test

# Com coverage
docker-compose exec frontend npm test -- --coverage
```

### Usando Makefile

```bash
make test              # Todos os testes
make backend-test      # Apenas backend
make frontend-test     # Apenas frontend
```

---

## 🔧 Comandos Úteis

```bash
make build         # Build das imagens
make up            # Iniciar serviços
make down          # Parar serviços
make logs          # Ver logs
make shell         # Shell do backend
make migrate       # Executar migrations
make test          # Executar testes
make clean         # Limpar containers e volumes
```

---

## 🏗 Arquitetura

```
payment-gateway-integration/
├── backend/                    # Microserviço Python/FastAPI
│   ├── app/
│   │   ├── api/               # Rotas da API
│   │   │   ├── routes/        # Endpoints (auth, payments, etc)
│   │   │   └── deps_auth.py   # Dependencies de autenticação
│   │   ├── core/              # Configurações centrais
│   │   ├── gateways/          # Implementações dos gateways
│   │   ├── middleware/        # Rate limiting, idempotency
│   │   ├── models/            # Modelos SQLAlchemy
│   │   ├── schemas/           # Schemas Pydantic
│   │   ├── services/          # Lógica de negócio
│   │   ├── main.py            # App FastAPI
│   │   └── worker.py          # Worker assíncrono
│   ├── alembic/               # Migrations
│   └── tests/                 # Testes
├── frontend/                  # Microserviço React/TypeScript
│   ├── src/
│   │   ├── pages/            # Dashboard, Payments, Reports
│   │   └── services/         # API client
│   └── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml            # Pipeline CI/CD
├── docker-compose.yml
└── README.md
```

---

## 🔒 Segurança

### Implementações de Segurança

✅ **Autenticação JWT** com tokens assinados  
✅ **RBAC** (Role-Based Access Control)  
✅ **Rate Limiting** para prevenir abuse  
✅ **Idempotency** para prevenir duplicação  
✅ **Webhook Signature Validation**  
✅ **Criptografia** de dados sensíveis  
✅ **PCI Compliance** - mascaramento de cartões  
✅ **HTTPS** obrigatório em produção  
✅ **SQL Injection** prevenção via ORM  
✅ **XSS** proteção no frontend

### Configuração de Produção

1. **Altere todas as chaves secretas**
2. **Use HTTPS** para todos os endpoints
3. **Configure firewall**
4. **Ative Sentry** para monitoring
5. **Configure backups** do PostgreSQL
6. **Use senhas fortes** para SMTP

---

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Resposta:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "healthy",
  "redis": "healthy"
}
```

### Sentry Integration

Configure o DSN do Sentry no `.env`:
```env
SENTRY_DSN=https://your-key@sentry.io/project-id
```

### Logs

Logs são armazenados em:
- `backend/logs/app.log` - Logs gerais
- `backend/logs/error.log` - Apenas erros

---

## 🔄 Migrations

```bash
# Criar nova migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Aplicar migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1

# Ver histórico
docker-compose exec backend alembic history
```

---

## 📧 Email Notifications

Configure SMTP no `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@payment-gateway.com
```

**Emails enviados automaticamente**:
- ✅ Payment successful
- ❌ Payment failed
- 💸 Refund processed
- 🔔 Subscription created
- ⏸️ Subscription cancelled
- ⚠️ Subscription payment failed

---

## 🔁 Pagamentos Recorrentes

```python
# Criar subscription
{
  "customer_email": "customer@example.com",
  "amount": 29.99,
  "currency": "USD",
  "billing_cycle": "monthly",  # daily, weekly, monthly, quarterly, yearly
  "trial_days": 7,
  "gateway": "stripe"
}
```

---

## 📝 License

MIT License

---

## 🤝 Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes sobre como contribuir.

---

## 🗺 Roadmap

### ✅ Implementado
- [x] Autenticação JWT + RBAC
- [x] Rate Limiting
- [x] Idempotency Keys
- [x] Pagamentos Recorrentes
- [x] Notificações por Email
- [x] Multi-tenancy
- [x] CI/CD Pipeline
- [x] Testes de Integração

### 🚧 Próximas Features
- [ ] Metrics com Prometheus
- [ ] Dashboards com Grafana
- [ ] Fraud Detection avançado
- [ ] Split Payments
- [ ] Kubernetes deployment
- [ ] SDK Clients (Python, JS)
- [ ] Exportação de relatórios (PDF/Excel)

---

## 📞 Suporte

Para suporte, abra uma issue no GitHub ou consulte a [documentação completa](PHASE_1_2_FEATURES.md).

---

**Made with ❤️ for production-ready payment processing**
