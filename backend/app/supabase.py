from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from pydantic import ValidationError

from .config import Settings
from .models import Aircraft


class SupabaseConfigError(RuntimeError):
    """Raised when Supabase credentials are missing."""


class SupabaseRequestError(RuntimeError):
    """Raised when Supabase does not return usable data."""


class SupabaseAircraftRepository:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _base_url(self) -> str:
        if not self.settings.supabase_url or not self.settings.supabase_key:
            raise SupabaseConfigError(
                "Configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY."
            )
        return f"{self.settings.supabase_url.rstrip('/')}/rest/v1/aeronaves"

    def list_aircrafts(self, ids: list[str] | None = None) -> list[Aircraft]:
        query = {
            "select": (
                "id,modelo,imagem_url,custo_aquisicao,custo_manutencao,"
                "custo_combustivel_hora,autonomia_km,pax,carga_kg"
            ),
            "order": "created_at.asc",
        }

        if ids:
            safe_ids = [item.strip() for item in ids if item.strip()]
            if not safe_ids:
                return []
            query["id"] = f"in.({','.join(safe_ids)})"

        url = f"{self._base_url()}?{urlencode(query)}"
        request = Request(
            url,
            headers={
                "apikey": self.settings.supabase_key or "",
                "Authorization": f"Bearer {self.settings.supabase_key}",
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise SupabaseRequestError(
                "Nao foi possivel buscar aeronaves no Supabase."
            ) from exc

        if not isinstance(payload, list):
            raise SupabaseRequestError("Supabase retornou um payload inesperado.")

        try:
            return [Aircraft.model_validate(item) for item in payload]
        except ValidationError as exc:
            raise SupabaseRequestError(
                "Supabase retornou aeronaves com dados ausentes ou invalidos."
            ) from exc
