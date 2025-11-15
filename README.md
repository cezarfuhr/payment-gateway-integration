# Payment Gateway Integration

Sistema unificado de integração com múltiplos gateways de pagamento, oferecendo uma API consistente para processar pagamentos através de diferentes provedores.

## 🚀 Features

- **Múltiplos Gateways**: Suporte para Stripe, PayPal, Mercado Pago e PagSeguro
- **Webhooks**: Sistema robusto de processamento de webhooks com validação de assinaturas
- **Retry Logic**: Mecanismo automático de retry com backoff exponencial usando Redis
- **Reporting**: Geração de relatórios detalhados sobre transações e performance
- **PCI Compliance**: Implementação de boas práticas de segurança para dados sensíveis
- **Logs Detalhados**: Sistema de logging estruturado com suporte a JSON
- **API RESTful**: API completamente documentada com OpenAPI/Swagger
- **Dashboard Web**: Interface React para gerenciamento de pagamentos

## 📋 Requisitos

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

## 🛠 Tecnologias

### Backend
- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para PostgreSQL
- **Pydantic**: Validação de dados
- **Redis**: Queue para retry logic
- **Stripe SDK**: Integração com Stripe
- **PayPal REST SDK**: Integração com PayPal
- **Mercado Pago SDK**: Integração com Mercado Pago

### Frontend
- **React 18**: Framework UI
- **TypeScript**: Type safety
- **React Query**: Gerenciamento de estado e cache
- **Axios**: Cliente HTTP
- **React Router**: Navegação

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

### 3. Inicie os serviços

```bash
docker-compose up -d
```

### 4. Acesse a aplicação

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## 📚 Documentação Completa

Veja a documentação completa em CONTRIBUTING.md

## 🧪 Testes

```bash
make test
```

## 📝 License

MIT License
