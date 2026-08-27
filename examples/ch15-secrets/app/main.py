from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Chapter 15 secrets")
SECRET_FILE = Path("/run/secrets/api_token")


def load_secret(path: Path = SECRET_FILE) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"secret file is unavailable: {path}") from exc
    if len(value) < 16:
        raise RuntimeError("secret must contain at least 16 characters")
    return value


@app.get("/health")
def health() -> dict[str, str]:
    try:
        load_secret()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="secret unavailable") from exc
    return {"status": "ok", "secret": "loaded-but-not-disclosed"}
