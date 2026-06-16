from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Aircraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    modelo: str
    imagem_url: str | None = None
    custo_aquisicao: float = Field(ge=0)
    custo_manutencao: float = Field(ge=0)
    custo_combustivel_hora: float = Field(ge=0)
    autonomia_km: float = Field(ge=0)
    pax: int = Field(ge=0)
    carga_kg: float = Field(ge=0)


class AircraftDebugResponse(BaseModel):
    id: str
    modelo: str
    imagem: str
    custo_aquisicao: float
    custo_manutencao: float
    custo_combustivel_hora: float
    autonomia_km: float
    pax: int
    carga_kg: float


class VikorWeights(BaseModel):
    aquisicao: float = Field(default=20, ge=0)
    manutencao: float = Field(default=20, ge=0)
    combustivel: float = Field(default=20, ge=0)
    pax: float = Field(default=20, ge=0)
    carga: float = Field(default=20, ge=0)


class AviationVikorRequest(BaseModel):
    destino: str = ""
    pesos: VikorWeights = Field(default_factory=VikorWeights)
    aeronaves_ids: list[str] = Field(default_factory=list)

    @field_validator("aeronaves_ids")
    @classmethod
    def validate_aircraft_ids(cls, values: list[str]) -> list[str]:
        normalized_ids: list[str] = []
        for value in values:
            try:
                normalized_ids.append(str(UUID(str(value))))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "aeronaves_ids deve conter apenas UUIDs validos."
                ) from exc
        return normalized_ids


class DestinationResponse(BaseModel):
    id: str
    nome: str
    uf: str
    aeroporto: str
    distancia_km: int


class RejectedAircraft(BaseModel):
    id: str
    modelo: str
    motivo: str


class AviationRankingItem(BaseModel):
    id: str
    modelo: str
    imagem: str
    Q: float
    S: float
    R: float


class AviationVikorResponse(BaseModel):
    distancia_km: int
    rejeitadas: list[RejectedAircraft]
    ranking: list[AviationRankingItem]
