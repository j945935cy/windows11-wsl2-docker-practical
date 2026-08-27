from __future__ import annotations

import os
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()


class NoteInput(BaseModel):
    body: str = Field(min_length=1, max_length=500)


def connection() -> psycopg.Connection:
    password_file = Path(os.environ["PGPASSWORD_FILE"])
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=password_file.read_text(encoding="utf-8").strip(),
        connect_timeout=2,
    )


@app.get("/health/live")
def live() -> dict[str, bool]:
    return {"live": True}


@app.get("/health/ready")
def ready() -> dict[str, bool]:
    try:
        with connection() as conn:
            conn.execute("SELECT 1")
    except (OSError, KeyError, ValueError, psycopg.Error) as exc:
        raise HTTPException(status_code=503, detail="database not ready") from exc
    return {"ready": True}


@app.post("/notes", status_code=201)
def create_note(note: NoteInput) -> dict[str, object]:
    body = note.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="body must not be blank")
    with connection() as conn:
        row = conn.execute(
            "INSERT INTO notes(body) VALUES (%s) RETURNING id, body", (body,)
        ).fetchone()
    assert row is not None
    return {"id": row[0], "body": row[1]}


@app.get("/notes")
def list_notes() -> list[dict[str, object]]:
    with connection() as conn:
        rows = conn.execute("SELECT id, body FROM notes ORDER BY id").fetchall()
    return [{"id": row[0], "body": row[1]} for row in rows]
