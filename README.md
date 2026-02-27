# 💰 Controle Financeiro ✈️

App Streamlit para organizar suas finanças.

## Como rodar

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Rode o app
streamlit run app.py
```

O app abre em `http://localhost:8501`.

## Arquitetura

A aplicação foi reorganizada para separar responsabilidades:

- `app.py`: entrypoint da aplicação
- `application/`: bootstrap de dependências e estado inicial da sessão
- `core/`: utilitários, modelos, constantes e settings (`fmt_brl`, dataclasses, `PluggySettings`)
- `ports/`: contratos de dependência (DIP), segregados por responsabilidade (`RulesDataPort`, `TransactionsDataPort`, `BankingPort`)
- `adapters/`: implementações concretas dos contratos (segregadas por regras/transações/integração bancária)
- `repositories/`: acesso a dados segregado (`ConfigRepository` e `TransactionsRepository`)
- `domain/`: regras de domínio puras (classificação, análise financeira e deduplicação)
- `services/`: casos de uso com dependência em portas
- `presentation/`: apresentação Streamlit (estilos, sidebar, componentes e tela principal)
- `presentation/tabs/`: renderização por aba (dashboard, transações, regras, análise, faturas)
- `data.py`: fachada de compatibilidade delegando para repositórios
- `pluggy_integration.py`: integração HTTP com API Pluggy

```text
files/
├── app.py
├── application/
│   └── bootstrap.py
├── adapters/
│   ├── transactions_data_adapter.py
│   ├── rules_data_adapter.py
│   └── pluggy_banking_adapter.py
├── repositories/
│   ├── config_repository.py
│   └── transactions_repository.py
├── domain/
│   ├── analytics.py
│   ├── classification.py
│   └── deduplication.py
├── core/
│   ├── constants.py
│   ├── formatting.py
│   ├── models.py
│   └── settings.py
├── ports/
│   ├── rules_port.py
│   ├── transactions_port.py
│   └── banking_port.py
├── services/
│   ├── finance_service.py
│   └── bills_service.py
├── presentation/
│   ├── styles.py
│   ├── sidebar.py
│   ├── components.py
│   ├── main_screen.py
│   └── tabs/
│       ├── dashboard_tab.py
│       ├── transactions_tab.py
│       ├── add_transaction_tab.py
│       ├── rules_tab.py
│       ├── analysis_tab.py
│       └── bills_tab.py
├── data.py  (fachada de compatibilidade para os repositórios)
├── pluggy_integration.py
├── tests/
│   ├── test_finance_service.py
│   ├── test_bills_service.py
│   ├── test_data_logic.py
│   └── test_domain_analytics.py
├── dados_financeiros.csv
└── regras_classificacao.json
```

## Princípios aplicados

- **Single Responsibility**: cada módulo/aba tem uma responsabilidade principal
- **Separation of Concerns**: UI desacoplada da lógica de negócio
- **Dependency Inversion**: `services` dependem de contratos (`ports`) e não de módulos concretos
- **Composition Root**: `application/bootstrap.py` injeta adapters concretos nos serviços
- **Manutenibilidade**: menor acoplamento e melhor legibilidade para evoluções
