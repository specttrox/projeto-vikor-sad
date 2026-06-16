from math import isfinite
from typing import Any


class VikorInputError(ValueError):
    """Raised when a VIKOR request cannot be calculated."""


CRITERIA = [
    ("aquisicao", "custo_aquisicao", "cost"),
    ("manutencao", "custo_manutencao", "cost"),
    ("combustivel", "custo_combustivel_hora", "cost"),
    ("pax", "pax", "benefit"),
    ("carga", "carga_kg", "benefit"),
]


def _get_value(aircraft: Any, field: str) -> float:
    try:
        if isinstance(aircraft, dict):
            value = aircraft[field]
        else:
            value = getattr(aircraft, field)
        numeric_value = float(value)
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise VikorInputError(
            f"Valor ausente ou invalido para {field}."
        ) from exc

    if not isfinite(numeric_value):
        raise VikorInputError(f"Valor invalido para {field}.")
    return numeric_value


def _get_text(aircraft: Any, field: str, default: str = "") -> str:
    if isinstance(aircraft, dict):
        value = aircraft.get(field, default)
    else:
        value = getattr(aircraft, field, default)
    return "" if value is None else str(value)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    selected = {name: float(weights.get(name, 0)) for name, _, _ in CRITERIA}
    if any(value < 0 for value in selected.values()):
        raise VikorInputError("Pesos nao podem ser negativos.")

    total = sum(selected.values())
    if total <= 0:
        raise VikorInputError("A soma dos pesos deve ser maior que zero.")

    return {name: value / total for name, value in selected.items()}


def calculate_aircraft_vikor(aircrafts: list[Any], weights: dict[str, float], v: float = 0.5):
    if not 0 <= v <= 1:
        raise VikorInputError("O parametro v deve estar entre 0 e 1.")
    if not aircrafts:
        raise VikorInputError("Nenhuma aeronave aprovada para ranqueamento.")

    normalized_weights = normalize_weights(weights)

    if len(aircrafts) == 1:
        aircraft = aircrafts[0]
        return [
            {
                "id": _get_text(aircraft, "id"),
                "modelo": _get_text(aircraft, "modelo"),
                "imagem": _get_text(aircraft, "imagem_url"),
                "Q": 0.0,
                "S": 0.0,
                "R": 0.0,
            }
        ]

    terms_by_aircraft = {_get_text(aircraft, "id"): [] for aircraft in aircrafts}

    for weight_key, aircraft_field, criterion_type in CRITERIA:
        values = [_get_value(aircraft, aircraft_field) for aircraft in aircrafts]
        best = min(values) if criterion_type == "cost" else max(values)
        worst = max(values) if criterion_type == "cost" else min(values)
        denominator = abs(best - worst)

        for aircraft, value in zip(aircrafts, values):
            aircraft_id = _get_text(aircraft, "id")
            if denominator == 0:
                regret_term = 0
            elif criterion_type == "cost":
                regret_term = normalized_weights[weight_key] * (value - best) / denominator
            else:
                regret_term = normalized_weights[weight_key] * (best - value) / denominator
            terms_by_aircraft[aircraft_id].append(regret_term)

    s_values = {
        aircraft_id: sum(terms)
        for aircraft_id, terms in terms_by_aircraft.items()
    }
    r_values = {
        aircraft_id: max(terms) if terms else 0
        for aircraft_id, terms in terms_by_aircraft.items()
    }

    s_min, s_max = min(s_values.values()), max(s_values.values())
    r_min, r_max = min(r_values.values()), max(r_values.values())

    ranking = []
    for aircraft in aircrafts:
        aircraft_id = _get_text(aircraft, "id")
        s_value = s_values[aircraft_id]
        r_value = r_values[aircraft_id]
        s_component = 0 if s_max == s_min else (s_value - s_min) / (s_max - s_min)
        r_component = 0 if r_max == r_min else (r_value - r_min) / (r_max - r_min)
        q_value = v * s_component + (1 - v) * r_component

        ranking.append(
            {
                "id": aircraft_id,
                "modelo": _get_text(aircraft, "modelo"),
                "imagem": _get_text(aircraft, "imagem_url"),
                "Q": round(q_value, 6),
                "S": round(s_value, 6),
                "R": round(r_value, 6),
            }
        )

    return sorted(ranking, key=lambda item: (item["Q"], item["S"], item["R"], item["modelo"]))
