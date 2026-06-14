from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.aviation import filter_by_autonomy
from app.geocoding import distance_from_recife_km
from app.models import Aircraft
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
    distance = distance_from_recife_km(
        "Natal, RN",
        "AeroVIKOR-tests/1.0",
    )

    assert 250 <= distance <= 270


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


if __name__ == "__main__":
    test_aircraft_vikor_prioritizes_capacity_when_weights_do()
    test_filter_by_autonomy_rejects_aircraft_below_distance()
    test_distance_from_recife_to_natal_uses_local_table()
    test_weights_must_have_positive_sum()
    test_vikor_requires_at_least_one_approved_aircraft()
    print("backend tests passed")
