from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .aviation import filter_by_autonomy
from .config import get_settings
from .geocoding import GeocodingError, distance_from_recife_km, list_destinations
from .models import (
    AircraftDebugResponse,
    AviationVikorRequest,
    AviationVikorResponse,
    DestinationResponse,
)
from .supabase import (
    SupabaseAircraftRepository,
    SupabaseConfigError,
    SupabaseRequestError,
)
from .vikor import VikorInputError, calculate_aircraft_vikor

settings = get_settings()
repository = SupabaseAircraftRepository(settings)

app = FastAPI(
    title="AeroVIKOR API",
    description=(
        "FastAPI backend for aircraft selection using the VIKOR method "
        "and offline route distances from Recife."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _aircraft_debug_response(aircraft):
    return AircraftDebugResponse(
        id=aircraft.id,
        modelo=aircraft.modelo,
        imagem=aircraft.imagem_url or "",
        custo_aquisicao=aircraft.custo_aquisicao,
        custo_manutencao=aircraft.custo_manutencao,
        custo_combustivel_hora=aircraft.custo_combustivel_hora,
        autonomia_km=aircraft.autonomia_km,
        pax=aircraft.pax,
        carga_kg=aircraft.carga_kg,
    )


def _map_backend_error(exc: Exception):
    if isinstance(exc, SupabaseConfigError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, SupabaseRequestError):
        return HTTPException(status_code=502, detail=str(exc))
    if isinstance(exc, GeocodingError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, VikorInputError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Erro inesperado no backend.")


@app.get("/health")
def health():
    return {"status": "ok", "service": "AeroVIKOR API"}


@app.get("/aircrafts", response_model=list[AircraftDebugResponse])
def list_aircrafts():
    try:
        return [_aircraft_debug_response(item) for item in repository.list_aircrafts()]
    except (SupabaseConfigError, SupabaseRequestError) as exc:
        raise _map_backend_error(exc) from exc


@app.get("/destinations", response_model=list[DestinationResponse])
def get_destinations():
    return list_destinations()


@app.post("/vikor", response_model=AviationVikorResponse)
def run_aircraft_vikor(payload: AviationVikorRequest):
    destino = payload.destino.strip()
    if not destino:
        raise HTTPException(status_code=400, detail="Informe um destino.")
    if not payload.aeronaves_ids:
        raise HTTPException(
            status_code=400,
            detail="Selecione ao menos uma aeronave.",
        )

    try:
        distance_km = distance_from_recife_km(destino)
        aircrafts = repository.list_aircrafts(ids=payload.aeronaves_ids)
        found_ids = {aircraft.id for aircraft in aircrafts}
        missing_ids = [
            aircraft_id
            for aircraft_id in payload.aeronaves_ids
            if aircraft_id not in found_ids
        ]
        if missing_ids:
            raise VikorInputError(
                "Aeronaves nao encontradas no Supabase: " + ", ".join(missing_ids)
            )

        approved, rejected = filter_by_autonomy(aircrafts, distance_km)
        if not approved:
            raise VikorInputError(
                "Nenhuma aeronave selecionada possui autonomia suficiente para este destino."
            )

        ranking = calculate_aircraft_vikor(
            aircrafts=approved,
            weights=payload.pesos.model_dump(),
            v=0.5,
        )
        return AviationVikorResponse(
            distancia_km=distance_km,
            rejeitadas=rejected,
            ranking=ranking,
        )
    except (
        SupabaseConfigError,
        SupabaseRequestError,
        GeocodingError,
        VikorInputError,
    ) as exc:
        raise _map_backend_error(exc) from exc
