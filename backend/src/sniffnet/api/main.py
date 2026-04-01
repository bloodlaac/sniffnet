from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from sniffnet.api.bootstrap import initialize_database
from sniffnet.api.config import APP_ORIGINS
from sniffnet.api.errors import register_error_handlers
from sniffnet.api.routes import auth, catalog, classifications, experiments, files, predict, users


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=APP_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)

api_prefix = "/api"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(catalog.router, prefix=api_prefix)
app.include_router(experiments.router, prefix=api_prefix)
app.include_router(files.router, prefix=api_prefix)
app.include_router(classifications.router, prefix=api_prefix)
app.include_router(predict.router, prefix=api_prefix)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/")
def get_main_page():
    return {"message": "Hello, World!"}


def main() -> None:
    initialize_database()
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()
