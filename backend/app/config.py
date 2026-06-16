from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None
    supabase_key: str | None
    allowed_origins: list[str]


LOCAL_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _split_origins(value: str | None) -> list[str]:
    if not value:
        return LOCAL_ALLOWED_ORIGINS

    origins = [item.strip() for item in value.split(",") if item.strip()]
    return origins or LOCAL_ALLOWED_ORIGINS


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        if key:
            os.environ.setdefault(key, value)


def get_settings() -> Settings:
    _load_env_file()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    return Settings(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        allowed_origins=_split_origins(os.getenv("ALLOWED_ORIGINS")),
    )
