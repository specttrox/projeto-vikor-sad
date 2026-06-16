import unicodedata
from dataclasses import asdict, dataclass


class GeocodingError(ValueError):
    """Raised when a destination is not available in the offline table."""


@dataclass(frozen=True)
class Destination:
    id: str
    nome: str
    uf: str
    aeroporto: str
    distancia_km: int


DESTINATIONS = [
    Destination("natal-rn", "Natal", "RN", "NAT - Aeroporto de Natal", 253),
    Destination("fortaleza-ce", "Fortaleza", "CE", "FOR - Aeroporto de Fortaleza", 630),
    Destination("joao-pessoa-pb", "Joao Pessoa", "PB", "JPA - Aeroporto de Joao Pessoa", 105),
    Destination("maceio-al", "Maceio", "AL", "MCZ - Aeroporto de Maceio", 203),
    Destination("aracaju-se", "Aracaju", "SE", "AJU - Aeroporto de Aracaju", 397),
    Destination("salvador-ba", "Salvador", "BA", "SSA - Aeroporto de Salvador", 676),
    Destination(
        "fernando-de-noronha-pe",
        "Fernando de Noronha",
        "PE",
        "FEN - Aeroporto de Fernando de Noronha",
        545,
    ),
    Destination("brasilia-df", "Brasilia", "DF", "BSB - Aeroporto de Brasilia", 1655),
    Destination("sao-paulo-sp", "Sao Paulo", "SP", "GRU/CGH - Aeroportos de Sao Paulo", 2128),
    Destination(
        "rio-de-janeiro-rj",
        "Rio de Janeiro",
        "RJ",
        "GIG/SDU - Aeroportos do Rio de Janeiro",
        1878,
    ),
    Destination("belo-horizonte-mg", "Belo Horizonte", "MG", "CNF - Aeroporto de Confins", 1641),
    Destination("campinas-sp", "Campinas", "SP", "VCP - Aeroporto de Viracopos", 2093),
    Destination("curitiba-pr", "Curitiba", "PR", "CWB - Aeroporto de Curitiba", 2459),
    Destination("porto-alegre-rs", "Porto Alegre", "RS", "POA - Aeroporto de Porto Alegre", 2978),
    Destination("belem-pa", "Belem", "PA", "BEL - Aeroporto de Belem", 1676),
    Destination("manaus-am", "Manaus", "AM", "MAO - Aeroporto de Manaus", 2840),
    Destination("teresina-pi", "Teresina", "PI", "THE - Aeroporto de Teresina", 934),
    Destination("sao-luis-ma", "Sao Luis", "MA", "SLZ - Aeroporto de Sao Luis", 1205),
    Destination("petrolina-pe", "Petrolina", "PE", "PNZ - Aeroporto de Petrolina", 637),
]


def normalize_place_name(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    cleaned = ascii_value.lower().replace(",", " ").replace("-", " ")
    return " ".join(cleaned.split())


def _destination_aliases(destination: Destination) -> set[str]:
    return {
        normalize_place_name(destination.id),
        normalize_place_name(destination.nome),
        normalize_place_name(f"{destination.nome} {destination.uf}"),
        normalize_place_name(f"{destination.nome}, {destination.uf}"),
    }


DESTINATIONS_BY_ALIAS = {
    alias: destination
    for destination in DESTINATIONS
    for alias in _destination_aliases(destination)
}


def list_destinations() -> list[dict[str, str | int]]:
    return [asdict(destination) for destination in DESTINATIONS]


def resolve_destination(value: str) -> Destination:
    normalized = normalize_place_name(value)
    if not normalized:
        raise GeocodingError("Informe um destino.")

    destination = DESTINATIONS_BY_ALIAS.get(normalized)
    if destination:
        return destination

    available = ", ".join(f"{item.nome}, {item.uf}" for item in DESTINATIONS)
    raise GeocodingError(
        "Destino indisponivel. Escolha um dos destinos pre-carregados: "
        f"{available}."
    )


def distance_from_recife_km(destination: str) -> int:
    return resolve_destination(destination).distancia_km
