from pydantic import BaseModel


class Settings(BaseModel):
    # Core
    language: str = "ar"

    # Storage
    sessions_dir: str = "data/sessions"

    # Safety / UX
    disclaimer: str = (
        "Viola provides CBT-style self-help guidance and emotional indicators. "
        "It is not a medical diagnosis or a substitute for professional care."
    )


settings = Settings()
