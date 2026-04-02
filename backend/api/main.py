from fastapi import FastAPI

from backend.services.registry import create_application_overview

app = FastAPI(
    title="Anki Card Maker API",
    version="0.1.0",
    description="Backend API for modular document-to-Anki flashcard generation.",
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/overview")
def overview() -> dict[str, object]:
    return create_application_overview()

