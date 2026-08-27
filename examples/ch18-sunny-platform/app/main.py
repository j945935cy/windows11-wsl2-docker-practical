from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from psycopg.rows import dict_row


class NoteInput(BaseModel):
    body: str = Field(min_length=1, max_length=500)

    @field_validator("body")
    @classmethod
    def body_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("body must not be blank")
        return cleaned


def database_config() -> dict[str, object]:
    password_path = os.getenv("DB_PASSWORD_FILE")
    if not password_path:
        raise RuntimeError("DB password file is not configured")
    try:
        password = Path(password_path).read_text(encoding="utf-8").strip()
    except OSError as error:
        raise RuntimeError("DB password file is not readable") from error
    if not password:
        raise RuntimeError("DB password file is empty")
    return {
        "host": os.getenv("PGHOST", "db"),
        "port": int(os.getenv("PGPORT", "5432")),
        "user": os.getenv("POSTGRES_USER", "sunny"),
        "password": password,
        "dbname": os.getenv("POSTGRES_DB", "sunny"),
        "row_factory": dict_row,
    }


class PostgresStore:
    def connection(self):
        return psycopg.connect(**database_config())

    def ping(self) -> bool:
        try:
            with self.connection() as connection:
                connection.execute("SELECT 1")
            return True
        except psycopg.Error:
            return False

    def create_note(self, body: str) -> dict[str, Any]:
        with self.connection() as connection:
            row = connection.execute(
                "INSERT INTO notes(body) VALUES (%s) RETURNING id, body", (body,)
            ).fetchone()
        if row is None:
            raise RuntimeError("database returned no inserted row")
        return dict(row)

    def list_notes(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT id, body FROM notes ORDER BY id").fetchall()
        return [dict(row) for row in rows]


def create_app(store=None) -> FastAPI:
    repository = store or PostgresStore()
    application = FastAPI(title="Sunny Platform", version="1.0.0")

    @application.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "alive"}

    @application.get("/health/ready")
    def ready() -> dict[str, str]:
        if not repository.ping():
            raise HTTPException(status_code=503, detail="database unavailable")
        return {"status": "ready"}

    @application.post("/notes", status_code=201)
    def create_note(note: NoteInput) -> dict[str, Any]:
        return repository.create_note(note.body)

    @application.get("/notes")
    def list_notes() -> list[dict[str, Any]]:
        return repository.list_notes()

    return application


app = create_app()
