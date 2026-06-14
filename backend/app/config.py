from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None
    supabase_key: str | None
    allowed_origins: list[str]
    geocoder_user_agent: str


def _split_origins(value: str | None) -> list[str]:
    if not value:
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

    origins = [item.strip() for item in value.split(",") if item.strip()]
    return origins or ["*"]


def get_settings() -> Settings:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    return Settings(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        allowed_origins=_split_origins(os.getenv("ALLOWED_ORIGINS")),
        geocoder_user_agent=os.getenv(
            "GEOCODER_USER_AGENT",
            "AeroVIKOR/1.0 academic project contact:no-reply@example.com",
        ),
    )
