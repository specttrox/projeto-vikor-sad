from math import asin, cos, radians, sin, sqrt
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import unicodedata


class GeocodingError(ValueError):
    """Raised when a destination cannot be converted to coordinates."""


RECIFE_COORDS = (-8.0476, -34.8770)

DESTINATION_COORDS = {
    "recife": RECIFE_COORDS,
    "recife pe": RECIFE_COORDS,
    "natal": (-5.7945, -35.2110),
    "natal rn": (-5.7945, -35.2110),
    "fortaleza": (-3.7319, -38.5267),
    "fortaleza ce": (-3.7319, -38.5267),
    "salvador": (-12.9777, -38.5016),
    "salvador ba": (-12.9777, -38.5016),
    "joao pessoa": (-7.1195, -34.8450),
    "joao pessoa pb": (-7.1195, -34.8450),
    "maceio": (-9.6498, -35.7089),
    "maceio al": (-9.6498, -35.7089),
    "aracaju": (-10.9472, -37.0731),
    "aracaju se": (-10.9472, -37.0731),
    "fernando de noronha": (-3.8549, -32.4230),
    "fernando de noronha pe": (-3.8549, -32.4230),
    "brasilia": (-15.7939, -47.8828),
    "brasilia df": (-15.7939, -47.8828),
    "sao paulo": (-23.5558, -46.6396),
    "sao paulo sp": (-23.5558, -46.6396),
    "rio de janeiro": (-22.9068, -43.1729),
    "rio de janeiro rj": (-22.9068, -43.1729),
    "belem": (-1.4558, -48.4902),
    "belem pa": (-1.4558, -48.4902),
    "manaus": (-3.1190, -60.0217),
    "manaus am": (-3.1190, -60.0217),
    "teresina": (-5.0919, -42.8034),
    "teresina pi": (-5.0919, -42.8034),
    "sao luis": (-2.5307, -44.3068),
    "sao luis ma": (-2.5307, -44.3068),
}


def normalize_place_name(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    cleaned = ascii_value.lower().replace(",", " ").replace("-", " ")
    return " ".join(cleaned.split())


def haversine_km(origin: tuple[float, float], destination: tuple[float, float]) -> float:
    origin_lat, origin_lon = origin
    dest_lat, dest_lon = destination
    radius_km = 6371.0

    d_lat = radians(dest_lat - origin_lat)
    d_lon = radians(dest_lon - origin_lon)
    lat1 = radians(origin_lat)
    lat2 = radians(dest_lat)

    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius_km * c


def geocode_destination(destination: str, user_agent: str) -> tuple[float, float]:
    normalized = normalize_place_name(destination)
    if not normalized:
        raise GeocodingError("Informe um destino.")

    if normalized in DESTINATION_COORDS:
        return DESTINATION_COORDS[normalized]

    params = urlencode(
        {
            "format": "jsonv2",
            "limit": "1",
            "countrycodes": "br",
            "q": destination,
        }
    )
    request = Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": user_agent, "Accept": "application/json"},
    )

    try:
        with urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise GeocodingError(
            "Nao foi possivel consultar o geocodificador para este destino."
        ) from exc

    if not data:
        raise GeocodingError(f"Destino nao encontrado: {destination}")

    try:
        return float(data[0]["lat"]), float(data[0]["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GeocodingError(
            "O geocodificador retornou uma resposta inesperada."
        ) from exc


def distance_from_recife_km(destination: str, user_agent: str) -> int:
    coords = geocode_destination(destination, user_agent)
    return round(haversine_km(RECIFE_COORDS, coords))
