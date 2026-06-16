# AeroVIKOR Decision Hub

Aplicacao Web para selecao multicriterio de aeronaves usando o metodo VIKOR.

O frontend permite cadastrar aeronaves no Supabase, escolher uma missao saindo de Recife, ajustar pesos de decisao e visualizar o ranking final. O backend FastAPI e o motor de decisao: calcula distancia, filtra autonomia e executa o VIKOR.

## Funcao do backend

O frontend esta pronto para chamar `POST /vikor`. Esse endpoint recebe:

- destino da missao;
- pesos dos criterios;
- IDs das aeronaves selecionadas.

O backend entao:

1. Busca as aeronaves no Supabase.
2. Consulta a distancia do destino em uma tabela offline do proprio projeto.
3. Remove aeronaves com autonomia insuficiente.
4. Aplica VIKOR nas aeronaves aprovadas.
5. Retorna ranking com `Q`, `S` e `R`.

O backend nao depende de API externa de geolocalizacao. O usuario escolhe ou
digita um dos destinos pre-carregados expostos por `GET /destinations`.

## Stack

- Frontend: React + TanStack Start + Vite
- Banco: Supabase/PostgreSQL
- Backend: FastAPI/Python
- Deploy sugerido: Frontend na Vercel ou Lovable, backend no Render

## Backend local

Requer Python 3.11+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Configure as variaveis de ambiente:

Opcao mais simples: copie `backend/.env.example` para `backend/.env` e preencha:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

Ou defina pelo PowerShell:

```powershell
$env:SUPABASE_URL="https://seu-projeto.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="sua_service_role_key"
$env:ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173"
```

Inicie a API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

URLs locais:

- API: http://localhost:8000
- Swagger/OpenAPI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Endpoints

### GET /health

Verifica se o backend esta no ar.

### GET /aircrafts

Lista aeronaves do Supabase para debug no Swagger.

### GET /destinations

Lista os destinos disponiveis partindo de Recife, com distancia aerea aproximada
em km. Exemplo de item:

```json
{
  "id": "natal-rn",
  "nome": "Natal",
  "uf": "RN",
  "aeroporto": "NAT - Aeroporto de Natal",
  "distancia_km": 253
}
```

### POST /vikor

Payload esperado pelo frontend:

```json
{
  "destino": "Natal, RN",
  "pesos": {
    "aquisicao": 20,
    "manutencao": 20,
    "combustivel": 20,
    "pax": 20,
    "carga": 20
  },
  "aeronaves_ids": ["uuid-1", "uuid-2"]
}
```

Resposta:

```json
{
  "distancia_km": 253,
  "rejeitadas": [
    {
      "id": "uuid-1",
      "modelo": "Aeronave X",
      "motivo": "Autonomia insuficiente: 200 km < 253 km"
    }
  ],
  "ranking": [
    {
      "id": "uuid-2",
      "modelo": "Aeronave Y",
      "imagem": "https://...",
      "Q": 0.0,
      "S": 0.0,
      "R": 0.0
    }
  ]
}
```

## Criterios VIKOR

Custos, onde menor e melhor:

- `custo_aquisicao`
- `custo_manutencao`
- `custo_combustivel_hora`

Beneficios, onde maior e melhor:

- `pax`
- `carga_kg`

Filtro eliminatorio:

- `autonomia_km` precisa ser maior ou igual a distancia da missao.

## Frontend local

O frontend fica em `frontend/` e foi feito com Bun/TanStack Start.

Como este PC nao tem Bun instalado, este caminho com npm tambem funciona:

```powershell
cd frontend
npm.cmd install --no-package-lock --legacy-peer-deps
npm.cmd run dev
```

Se voce tiver Bun instalado, use:

```powershell
cd frontend
bun install
bun dev
```

Configure as variaveis do frontend:

Copie `frontend/.env.example` para `frontend/.env` e preencha:

```env
VITE_SUPABASE_URL=https://seu-projeto.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sua_publishable_key
VITE_AVIATION_API_URL=http://localhost:8000
```

## Deploy do backend no Render

Crie um Web Service no Render apontando para o repositorio.

Configuracao:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Variaveis no Render:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ALLOWED_ORIGINS=https://seu-frontend.vercel.app`

No plano gratuito do Render, a API pode dormir apos alguns minutos sem requisicoes. A primeira chamada depois disso pode demorar mais.

## Deploy do frontend

Na Vercel ou Lovable, configure:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`
- `VITE_AVIATION_API_URL=https://seu-backend.onrender.com`

Depois de alterar variaveis de ambiente, faca um novo deploy.

## Testes

```powershell
cd backend
.\.venv\Scripts\python.exe tests\test_vikor.py
```

Ou, se estiver usando outro Python com as dependencias instaladas:

```powershell
python tests\test_vikor.py
```
