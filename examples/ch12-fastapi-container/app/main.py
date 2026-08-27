from fastapi import FastAPI

app = FastAPI(title="Chapter 12 FastAPI container")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello from FastAPI in Docker"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
