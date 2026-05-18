# Manhã com Deus — MVP

App devocional com IA usando FastAPI + Claude (Anthropic).

## Estrutura

```
manha-com-deus/
├── main.py              ← FastAPI backend
├── requirements.txt     ← dependências Python
├── .env                 ← variáveis locais (NÃO sobe pro GitHub)
├── .gitignore
├── frontend/
│   └── index.html       ← app frontend
└── README.md
```

## Rodar localmente

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar arquivo .env
echo "ANTHROPIC_API_KEY=sua_key_aqui" > .env

# 4. Rodar
uvicorn main:app --reload
```

Acesse: http://localhost:8000

## Deploy no Render

1. Suba o projeto no GitHub
2. No Render: New → Web Service → conecte o repositório
3. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Em **Environment Variables** adicione:
   - `ANTHROPIC_API_KEY` = sua key
5. Clique Deploy

## Variáveis de ambiente necessárias

| Variável | Descrição |
|----------|-----------|
| `ANTHROPIC_API_KEY` | Chave da API Anthropic |
