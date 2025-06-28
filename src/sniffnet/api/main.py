from fastapi import FastAPI
from fastapi.responses import FileResponse

from sniffnet.api.routes import (
    datasets,
    experiments,
    metrics,
    models,
    training_configs,
    users,
)

import uvicorn


app = FastAPI()

app.include_router(datasets.router)
app.include_router(experiments.router)
app.include_router(metrics.router)
app.include_router(models.router)
app.include_router(training_configs.router)
app.include_router(users.router)

@app.get("/")
def get_main_page():
    return {"message": "Hello, World!"}

def main() -> None:
    uvicorn.run(app)

if __name__ == "__main__":
    main()