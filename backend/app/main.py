import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import attempts, beans, methods

DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"

app = FastAPI(
    title="CoffeeLogs API",
    version="0.1.0",
    description="Track coffee beans, the methods you brew them with, and every attempt.",
)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

# PATCH and DELETE are preflighted, so leaving them out of allow_methods breaks the star
# toggle and delete while GETs keep working.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(beans.router)
app.include_router(methods.router)
app.include_router(attempts.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
