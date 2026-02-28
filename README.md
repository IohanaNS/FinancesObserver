# FinancesObserver

Aplicativo Streamlit para controle financeiro pessoal, com foco em:

- visão consolidada de gastos/entradas;
- categorização automática por regras;
- edição e reclassificação de transações;
- integração opcional com Pluggy para sincronizar transações e faturas.

## Funcionalidades

- Dashboard com KPIs de renda, gastos reais, percentual da renda consumido e total investido.
- Filtros por período, categoria e fonte.
- Sincronização de transações via Pluggy com deduplicação.
- Gestão manual de transações (adicionar e remover).
- Edição de categoria direto na tabela de transações.
- Regras de classificação por palavra-chave (com prioridade para regras mais específicas).
- Reclassificação em massa das transações já existentes.
- Análises por categoria, dia, fonte, assinaturas e simulador de economia.
- Consulta de faturas/limite de cartões via Pluggy, com cache local.
- Exportação de transações para CSV e Excel.

## Arquitetura

O projeto segue arquitetura em camadas:

- `presentation/`: interface Streamlit (componentes, sidebar, tabs).
- `services/`: casos de uso e orquestração da aplicação.
- `ports/`: contratos de entrada/saída para isolamento de dependências.
- `adapters/`: implementações concretas dos contratos.
- `repositories/`: persistência em arquivos (`csv`/`json`).
- `domain/`: regras puras de negócio (classificação, analytics, deduplicação).
- `application/`: composição de dependências (bootstrap).
- `core/`: constantes, modelos e utilitários.
- `data.py`: camada legado de compatibilidade (não expandir).

## Pré-requisitos

- Python 3.10+
- `pip`

## Instalação e execução

```bash
# 1) (Opcional, recomendado) criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate

# 2) Instalar dependências
pip install -r requirements.txt

# 3) Subir aplicação
streamlit run app.py
```

Aplicação disponível em `http://localhost:8501`.

## Configuração Pluggy (opcional)

Sem credenciais do Pluggy o app continua funcionando para gestão manual local.

### 1. Configure variáveis de ambiente

```bash
cp .env.example .env
```

Preencha no `.env`:

- `PLUGGY_CLIENT_ID`
- `PLUGGY_CLIENT_SECRET`
- `PLUGGY_BASE_URL` (opcional, padrão: `https://api.pluggy.ai`)
- `PLUGGY_BILLS_CACHE_FILE` (opcional, padrão: `faturas_cache.json`)
- `PLUGGY_ACCOUNTS_FILE` (opcional, padrão: `contas.json`)

### 2. Configure contas conectadas (`contas.json`)

```bash
cp contas.json.example contas.json
```

Estrutura esperada:

```json
{
  "contas": [
    {
      "pluggy_item_id": "seu-item-id",
      "nome": "Nubank"
    }
  ]
}
```

Fallback legado: se `contas.json` não existir, o app tenta `PLUGGY_ITEM_ID_NUBANK` e `PLUGGY_ITEM_ID_SANTANDER`.

## Estrutura de dados local

- `dados_financeiros.csv`: base principal de transações (criada automaticamente no primeiro uso).
- `regras_classificacao.json`: categorias e regras de classificação.
- `faturas_cache.json`: cache local da aba de faturas (quando Pluggy estiver habilitado).

## Comandos de desenvolvimento

```bash
# Executar todos os testes
python -m unittest discover -s tests -p "test_*.py" -v
```

```bash
# Checagem rápida de sintaxe
python -m py_compile app.py application/*.py core/*.py domain/*.py services/*.py adapters/*.py repositories/*.py ports/*.py presentation/*.py presentation/tabs/*.py tests/*.py data.py pluggy_integration.py
```

## Organização do código

```text
.
├── app.py
├── application/
├── presentation/
│   └── tabs/
├── services/
├── ports/
├── adapters/
├── repositories/
├── domain/
├── core/
├── tests/
├── data.py
└── pluggy_integration.py
```

## Segurança

- Não commitar `.env` ou credenciais.
- Tratar `dados_financeiros.csv` e `faturas_cache.json` como dados sensíveis.
- Evitar expor `contas.json` com identificadores reais de contas.
