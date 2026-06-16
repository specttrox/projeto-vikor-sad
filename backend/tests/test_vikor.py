from pathlib import Path
import sys

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.aviation import filter_by_autonomy
from app.geocoding import GeocodingError, distance_from_recife_km, list_destinations
from app.models import Aircraft, AviationVikorRequest
from app.vikor import VikorInputError, calculate_aircraft_vikor, normalize_weights


def sample_aircrafts():
    return [
        Aircraft(
            id="cheap",
            modelo="Econ 100",
            imagem_url="https://example.com/econ.jpg",
            custo_aquisicao=100,
            custo_manutencao=10,
            custo_combustivel_hora=40,
            autonomia_km=800,
            pax=4,
            carga_kg=250,
        ),
        Aircraft(
            id="balanced",
            modelo="Balanced 300",
            imagem_url="https://example.com/balanced.jpg",
            custo_aquisicao=180,
            custo_manutencao=18,
            custo_combustivel_hora=55,
            autonomia_km=1200,
            pax=8,
            carga_kg=650,
        ),
        Aircraft(
            id="cargo",
            modelo="Cargo 500",
            imagem_url="https://example.com/cargo.jpg",
            custo_aquisicao=260,
            custo_manutencao=24,
            custo_combustivel_hora=65,
            autonomia_km=1600,
            pax=6,
            carga_kg=1200,
        ),
    ]


def test_aircraft_vikor_prioritizes_capacity_when_weights_do():
    ranking = calculate_aircraft_vikor(
        sample_aircrafts(),
        {
            "aquisicao": 5,
            "manutencao": 5,
            "combustivel": 5,
            "pax": 35,
            "carga": 50,
        },
    )

    assert ranking[0]["id"] == "cargo"
    assert ranking[0]["Q"] <= ranking[1]["Q"]
    assert set(ranking[0].keys()) == {"id", "modelo", "imagem", "Q", "S", "R"}


def test_filter_by_autonomy_rejects_aircraft_below_distance():
    approved, rejected = filter_by_autonomy(sample_aircrafts(), distance_km=1000)

    assert [item.id for item in approved] == ["balanced", "cargo"]
    assert rejected[0].id == "cheap"
    assert "Autonomia insuficiente" in rejected[0].motivo


def test_distance_from_recife_to_natal_uses_local_table():
    distance = distance_from_recife_km("Natal, RN")

    assert 250 <= distance <= 270


def test_destinations_endpoint_data_has_natal():
    destinations = list_destinations()

    assert any(item["id"] == "natal-rn" for item in destinations)


def test_invalid_destination_is_rejected_without_external_api():
    try:
        distance_from_recife_km("Destino Inventado")
    except GeocodingError as exc:
        assert "Destino indisponivel" in str(exc)
    else:
        raise AssertionError("Expected GeocodingError")


def test_weights_must_have_positive_sum():
    try:
        normalize_weights(
            {
                "aquisicao": 0,
                "manutencao": 0,
                "combustivel": 0,
                "pax": 0,
                "carga": 0,
            }
        )
    except VikorInputError as exc:
        assert "soma dos pesos" in str(exc)
    else:
        raise AssertionError("Expected VikorInputError")


def test_vikor_requires_at_least_one_approved_aircraft():
    try:
        calculate_aircraft_vikor(
            [],
            {
                "aquisicao": 20,
                "manutencao": 20,
                "combustivel": 20,
                "pax": 20,
                "carga": 20,
            },
        )
    except VikorInputError as exc:
        assert "Nenhuma aeronave aprovada" in str(exc)
    else:
        raise AssertionError("Expected VikorInputError")


def test_vikor_reports_missing_aircraft_field_as_input_error():
    aircrafts = [
        {
            "id": "a",
            "modelo": "A",
            "imagem_url": "",
            "custo_aquisicao": 100,
            "custo_manutencao": 10,
            "custo_combustivel_hora": 20,
            "pax": 4,
            "carga_kg": 100,
        },
        {
            "id": "b",
            "modelo": "B",
            "imagem_url": "",
            "custo_aquisicao": 120,
            "custo_manutencao": 12,
            "custo_combustivel_hora": 22,
            "pax": 5,
        },
    ]

    try:
        calculate_aircraft_vikor(
            aircrafts,
            {
                "aquisicao": 20,
                "manutencao": 20,
                "combustivel": 20,
                "pax": 20,
                "carga": 20,
            },
        )
    except VikorInputError as exc:
        assert "carga_kg" in str(exc)
    else:
        raise AssertionError("Expected VikorInputError")


def test_request_rejects_invalid_aircraft_uuid():
    try:
        AviationVikorRequest(
            destino="Natal, RN",
            aeronaves_ids=["nao-e-uuid"],
        )
    except ValidationError as exc:
        assert "aeronaves_ids" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


if __name__ == "__main__":
    test_aircraft_vikor_prioritizes_capacity_when_weights_do()
    test_filter_by_autonomy_rejects_aircraft_below_distance()
    test_distance_from_recife_to_natal_uses_local_table()
    test_destinations_endpoint_data_has_natal()
    test_invalid_destination_is_rejected_without_external_api()
    test_weights_must_have_positive_sum()
    test_vikor_requires_at_least_one_approved_aircraft()
    test_vikor_reports_missing_aircraft_field_as_input_error()
    test_request_rejects_invalid_aircraft_uuid()
    print("backend tests passed")
