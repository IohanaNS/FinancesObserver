# FinancesObserver

Aplicativo Streamlit para controle financeiro pessoal, com foco em:

- visão consolidada de gastos/entradas;
- categorização automática por regras;
- edição e reclassificação de transações;
- integração opcional com Pluggy para sincronizar transações, saldos, investimentos e faturas.

## Funcionalidades

- Dashboard com KPIs de renda, gastos reais, percentual da renda consumido e total investido.
- Filtros por período, categoria e fonte.
- Sincronização de transações via Pluggy com deduplicação.
- Gestão manual de transações (adicionar e remover).
- Edição de categoria direto na tabela de transações.
- Regras de classificação por palavra-chave (com prioridade para regras mais específicas).
- Reclassificação em massa das transações já existentes.
- Análises por categoria, dia, fonte, assinaturas e simulador de economia.
- Contexto de investimentos para acompanhar carteira/caixinhas e progresso da meta financeira.
- Consulta de saldos de contas bancárias via Pluggy.
- Consulta de faturas/limite de cartões via Pluggy, com cache local.
- Gerenciamento de contas bancárias pela sidebar (adicionar/remover sem editar `contas.json` manualmente).
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

### Qual tipo de acesso escolher?

| Perfil | Solução | Custo |
|--------|---------|-------|
| Desenvolvedor (uso pessoal) | **MeuPluggy** | Gratuito |
| Pessoa Física/Jurídica (uso comercial) | Assinatura Paga | Conforme plano |

Para uso pessoal, utilize o **MeuPluggy** — acesso gratuito e sem limitações de trial.

### Configuração via MeuPluggy (recomendado para uso pessoal)

1. Crie uma conta no [MeuPluggy](https://meu.pluggy.ai) e conecte seus bancos pessoais.
2. Acesse o [Dashboard Pluggy](https://dashboard.pluggy.ai) e crie uma **Aplicação de Desenvolvimento**.
   - Selecione o conector **MeuPluggy** na lista de conectores.
   - Anote o `client_id` e `client_secret` gerados.
3. No Dashboard, use a **Autorização OAuth** para vincular sua conta MeuPluggy à aplicação de desenvolvimento.
   - Repita o processo de autorização para cada banco conectado no MeuPluggy (uma vez por banco, não por conta).
4. Após a autorização, os Items (conexões bancárias) aparecerão na sua aplicação de desenvolvimento. Anote os `item_id` de cada um.
5. Configure o projeto:

```bash
cp .env.example .env
```

Preencha no `.env`:

- `PLUGGY_CLIENT_ID` — da sua aplicação de desenvolvimento no Dashboard
- `PLUGGY_CLIENT_SECRET` — da sua aplicação de desenvolvimento no Dashboard

6. Configure as contas em `contas.json` (pela sidebar do app ou manualmente):

```bash
cp contas.json.example contas.json
```

```json
{
  "contas": [
    {
      "pluggy_item_id": "item-id-obtido-no-dashboard",
      "nome": "Nubank"
    }
  ]
}
```

Os dados são atualizados automaticamente uma vez por dia pelo MeuPluggy.

Para mais detalhes, consulte o [repositório MeuPluggy](https://github.com/pluggyai/meu-pluggy).

### Variáveis de ambiente opcionais

- `PLUGGY_BASE_URL` (padrão: `https://api.pluggy.ai`)
- `PLUGGY_BILLS_CACHE_FILE` (padrão: `faturas_cache.json`)
- `PLUGGY_BALANCES_CACHE_FILE` (padrão: `saldos_cache.json`)
- `PLUGGY_INVESTMENTS_CACHE_FILE` (padrão: `investimentos_cache.json`)
- `PLUGGY_ACCOUNTS_FILE` (padrão: `contas.json`)

### Fallback legado

Se `contas.json` não existir, o app tenta `PLUGGY_ITEM_ID_NUBANK` e `PLUGGY_ITEM_ID_SANTANDER` do `.env`.

## Estrutura de dados local

- `dados_financeiros.csv`: base principal de transações (criada automaticamente no primeiro uso).
- `regras_classificacao.json`: categorias e regras de classificação.
- `saldos_cache.json`: cache local da aba de saldos (quando Pluggy estiver habilitado).
- `investimentos_cache.json`: cache local da aba de investimentos (quando Pluggy estiver habilitado).
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
- Tratar `dados_financeiros.csv`, `saldos_cache.json`, `investimentos_cache.json` e `faturas_cache.json` como dados sensíveis.
- Evitar expor `contas.json` com identificadores reais de contas.
