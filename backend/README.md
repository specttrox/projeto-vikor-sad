# Backend AeroVIKOR

Backend FastAPI responsavel pela decisao multicriterio de aeronaves.

Ele nao cadastra aeronaves. O frontend continua cadastrando e listando aeronaves
diretamente no Supabase. O papel do backend e buscar as aeronaves selecionadas,
validar o destino, filtrar autonomia e calcular o ranking VIKOR.

## Rodar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Configure as variaveis descritas em `.env.example`.
Voce pode copiar `.env.example` para `.env`; o backend carrega esse arquivo
automaticamente ao iniciar.

## Contrato principal

`GET /destinations` retorna os destinos pre-carregados a partir de Recife.

`POST /vikor` recebe destino, pesos e IDs de aeronaves. A resposta possui:

- `distancia_km`
- `rejeitadas`
- `ranking` com `Q`, `S`, `R`

Esse e o endpoint consumido pelo frontend atual.

O backend nao usa API externa de geolocalizacao. As distancias sao dados fixos
do proprio projeto.
