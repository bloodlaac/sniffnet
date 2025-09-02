from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sniffnet.api.deps import get_database
from sniffnet.database.db_models import (
    User,
    Experiment,
    Dataset,
    TrainingConfig,
    Model,
    Metric
)

from sniffnet.api.routes import (
    datasets,
    experiments,
    metrics,
    models,
    training_configs,
    users,
    auth
)

import uvicorn

db: Session = next(get_database())

# new_users = [
#     User(username = "awesome_alex", email = "awesome@gmail.com", password="1"),
#     User(username = "Vector", email = "vector@mail.ru", password="2"),
#     User(username = "flawless", email = "flawless@gmail.com", password="3"),
#     User(username = "comfy", email = "comfy@mail.ru", password="4")
# ]

# db.add_all(new_users)
# db.commit()

# new_datasets = [
#     Dataset(
#         name = "FoodDataset",
#         classes_num = 20,
#         source = "http://datasets.com"
#     )
# ]

# db.add_all(new_datasets)
# db.commit()

# new_configs = [
#     TrainingConfig(
#         epochs_num = 15,
#         batch_size = 64,
#         loss_function = "MSELoss",
#         learning_rate = 0.01,
#         optimizer = "Adam",
#         layers_num = 32,
#         neurons_num = 200
#     ),
#     TrainingConfig(
#         epochs_num = 40,
#         batch_size = 32,
#         loss_function = "MSELoss",
#         learning_rate = 0.001,
#         optimizer = "Adam",
#         layers_num = 18,
#         neurons_num = 64
#     ),
#     TrainingConfig(
#         epochs_num = 10,
#         batch_size = 128,
#         loss_function = "BCE",
#         learning_rate = 0.01,
#         optimizer = "Adam",
#         layers_num = 20,
#         neurons_num = 100
#     ),
# ]

# db.add_all(new_configs)
# db.commit()

# new_experiments = [
#     Experiment(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[0].config_id,
#         user_id = new_users[0].user_id,
#         start_time = datetime(2025, 7, 1, 15, 30, 10),
#         end_time = datetime(2025, 7, 1, 15, 50, 10)
#     ),
#     Experiment(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[1].config_id,
#         user_id = new_users[1].user_id,
#         start_time = datetime(2025, 5, 28, 10, 15, 10),
#         end_time = datetime(2025, 5, 28, 10, 50, 10)
#     ),
#     Experiment(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[2].config_id,
#         user_id = new_users[2].user_id,
#         start_time = datetime(2025, 2, 20, 10, 15, 10),
#         end_time = datetime(2025, 2, 20, 10, 50, 10)
#     )
# ]

# db.add_all(new_experiments)
# db.commit()

# new_models = [
#     Model(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[0].config_id,
#         params_num = 1200000,
#         weights = b"123",
#         name = "ResNet18",
#         training_time = new_experiments[0].end_time - new_experiments[0].start_time
#     ),
#     Model(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[1].config_id,
#         params_num = 1000000,
#         weights = b"45",
#         name = "ResNet18",
#         training_time = new_experiments[0].end_time - new_experiments[0].start_time
#     ),
#     Model(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[2].config_id,
#         params_num = 100000,
#         weights = b"98",
#         name = "ResNet18",
#         training_time = new_experiments[0].end_time - new_experiments[0].start_time
#     )
# ]

# db.add_all(new_models)
# db.commit()

# new_metrics = [
#     Metric(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[0].config_id,
#         train_accuracy = 0.8934,
#         train_loss = 2.7936
#     ),
#     Metric(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[1].config_id,
#         train_accuracy = 0.5629,
#         train_loss = 3.2050
#     ),
#     Metric(
#         dataset_id = new_datasets[0].dataset_id,
#         config_id = new_configs[2].config_id,
#         train_accuracy = 0.9527,
#         train_loss = 1.0045
#     )
# ]

# db.add_all(new_metrics)
# db.commit()

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(experiments.router)
app.include_router(metrics.router)
app.include_router(models.router)
app.include_router(training_configs.router)
app.include_router(users.router)
app.include_router(auth.router)

@app.get("/")
def get_main_page():
    return {"message": "Hello, World!"}

def main() -> None:
    uvicorn.run(app, host="localhost", port=7142)

if __name__ == "__main__":
    main()