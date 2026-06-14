# Backend AeroVIKOR

Backend FastAPI responsavel pela decisao multicriterio de aeronaves.

## Rodar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Configure as variaveis descritas em `.env.example`.

## Contrato principal

`POST /vikor` recebe destino, pesos e IDs de aeronaves. A resposta possui:

- `distancia_km`
- `rejeitadas`
- `ranking` com `Q`, `S`, `R`

Esse e o endpoint consumido pelo frontend atual.
