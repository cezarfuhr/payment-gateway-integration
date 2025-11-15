# Guia de Contribuição

Obrigado por considerar contribuir com o Payment Gateway Integration! Este documento fornece diretrizes para contribuições.

## Como Contribuir

### Reportando Bugs

- Use o GitHub Issues para reportar bugs
- Descreva o bug em detalhes
- Inclua passos para reproduzir
- Inclua versões de software relevantes
- Adicione screenshots se aplicável

### Sugerindo Melhorias

- Use o GitHub Issues com a tag "enhancement"
- Descreva claramente a melhoria proposta
- Explique por que seria útil
- Forneça exemplos de uso

### Pull Requests

1. Fork o repositório
2. Crie uma branch a partir de `main`
3. Faça suas alterações
4. Adicione/atualize testes
5. Atualize a documentação
6. Certifique-se de que todos os testes passam
7. Faça commit seguindo o padrão
8. Push para sua fork
9. Abra um Pull Request

## Padrões de Código

### Backend (Python)

- Siga PEP 8
- Use type hints
- Docstrings para funções públicas
- Máximo 100 caracteres por linha
- Use Black para formatação
- Use isort para imports

```bash
# Formatar código
black app/
isort app/

# Verificar código
flake8 app/
mypy app/
```

### Frontend (TypeScript)

- Use TypeScript strict mode
- Componentes funcionais com hooks
- Props tipadas
- ESLint + Prettier

```bash
# Verificar código
npm run lint
npm run type-check
```

### Git Commit Messages

Formato: `<type>(<scope>): <subject>`

Tipos:
- `feat`: Nova feature
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Manutenção

Exemplos:
```
feat(payments): add Stripe payment support
fix(webhooks): validate signature correctly
docs(readme): update installation steps
```

## Testes

### Backend

```bash
# Executar todos os testes
pytest

# Com coverage
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_payments.py
```

### Frontend

```bash
# Executar testes
npm test

# Com coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

## Documentação

- Atualize README.md se necessário
- Adicione docstrings em Python
- Comente código complexo
- Atualize API docs se adicionar endpoints

## Code Review

Pull Requests serão revisados quanto a:

- Funcionalidade
- Qualidade do código
- Testes adequados
- Documentação
- Performance
- Segurança

## Questões?

Abra uma issue ou entre em contato com os mantenedores.
