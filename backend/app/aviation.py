from .models import Aircraft, RejectedAircraft


def filter_by_autonomy(aircrafts: list[Aircraft], distance_km: int):
    approved: list[Aircraft] = []
    rejected: list[RejectedAircraft] = []

    for aircraft in aircrafts:
        if aircraft.autonomia_km >= distance_km:
            approved.append(aircraft)
        else:
            rejected.append(
                RejectedAircraft(
                    id=aircraft.id,
                    modelo=aircraft.modelo,
                    motivo=(
                        f"Autonomia insuficiente: "
                        f"{round(aircraft.autonomia_km)} km < {distance_km} km"
                    ),
                )
            )

    return approved, rejected
