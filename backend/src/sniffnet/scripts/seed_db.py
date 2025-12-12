from datetime import datetime
from sqlalchemy import or_

from sniffnet.database.db import SessionLocal
from sniffnet.database.db_models import (
    Dataset,
    Experiment,
    Metric,
    Model,
    TrainingConfig,
    User,
)


def seed() -> None:
    session = SessionLocal()

    try:
        users_data = [
            {"username": "awesome_alex", "email": "awesome@gmail.com", "password": "1"},
            {"username": "Vector", "email": "vector@mail.ru", "password": "2"},
            {"username": "flawless", "email": "flawless@gmail.com", "password": "3"},
            {"username": "comfy", "email": "comfy@mail.ru", "password": "4"},
        ]
        user_objs: dict[str, User] = {}
        for data in users_data:
            existing = (
                session.query(User)
                .filter(or_(User.email == data["email"], User.username == data["username"]))
                .first()
            )
            if existing:
                user_objs[data["username"]] = existing
                continue

            user = User(**data)
            session.add(user)
            session.flush()
            user_objs[data["username"]] = user

        dataset_data = {
            "name": "FoodDataset",
            "classes_num": 20,
            "source": "http://datasets.com",
        }
        dataset = session.query(Dataset).filter_by(name=dataset_data["name"]).first()
        if not dataset:
            dataset = Dataset(**dataset_data)
            session.add(dataset)
            session.flush()

        configs_data = [
            {
                "epochs_num": 15,
                "batch_size": 64,
                "loss_function": "MSELoss",
                "learning_rate": 0.01,
                "optimizer": "Adam",
                "layers_num": 32,
                "neurons_num": 200,
            },
            {
                "epochs_num": 40,
                "batch_size": 32,
                "loss_function": "MSELoss",
                "learning_rate": 0.001,
                "optimizer": "Adam",
                "layers_num": 18,
                "neurons_num": 64,
            },
            {
                "epochs_num": 10,
                "batch_size": 128,
                "loss_function": "BCE",
                "learning_rate": 0.01,
                "optimizer": "Adam",
                "layers_num": 20,
                "neurons_num": 100,
            },
        ]

        configs: list[TrainingConfig] = []
        for config_data in configs_data:
            existing = (
                session.query(TrainingConfig)
                .filter_by(
                    epochs_num=config_data["epochs_num"],
                    batch_size=config_data["batch_size"],
                    loss_function=config_data["loss_function"],
                    learning_rate=config_data["learning_rate"],
                    optimizer=config_data["optimizer"],
                    layers_num=config_data["layers_num"],
                    neurons_num=config_data["neurons_num"],
                )
                .first()
            )
            if existing:
                configs.append(existing)
                continue

            config = TrainingConfig(**config_data)
            session.add(config)
            session.flush()
            configs.append(config)

        experiments_data = [
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[0].config_id,
                "user_id": user_objs["awesome_alex"].user_id,
                "start_time": datetime(2025, 7, 1, 15, 30, 10),
                "end_time": datetime(2025, 7, 1, 15, 50, 10),
            },
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[1].config_id,
                "user_id": user_objs["Vector"].user_id,
                "start_time": datetime(2025, 5, 28, 10, 15, 10),
                "end_time": datetime(2025, 5, 28, 10, 50, 10),
            },
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[2].config_id,
                "user_id": user_objs["flawless"].user_id,
                "start_time": datetime(2025, 2, 20, 10, 15, 10),
                "end_time": datetime(2025, 2, 20, 10, 50, 10),
            },
        ]

        experiments: list[Experiment] = []
        for exp_data in experiments_data:
            existing = (
                session.query(Experiment)
                .filter_by(
                    dataset_id=exp_data["dataset_id"],
                    config_id=exp_data["config_id"],
                    user_id=exp_data["user_id"],
                )
                .first()
            )
            if existing:
                experiments.append(existing)
                continue

            experiment = Experiment(**exp_data)
            session.add(experiment)
            session.flush()
            experiments.append(experiment)

        models_data = [
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[0].config_id,
                "params_num": 1200000,
                "weights": b"123",
                "name": "ResNet18",
                "training_time": experiments[0].end_time - experiments[0].start_time,
            },
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[1].config_id,
                "params_num": 1000000,
                "weights": b"45",
                "name": "ResNet18",
                "training_time": experiments[0].end_time - experiments[0].start_time,
            },
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[2].config_id,
                "params_num": 100000,
                "weights": b"98",
                "name": "ResNet18",
                "training_time": experiments[0].end_time - experiments[0].start_time,
            },
        ]

        for model_data in models_data:
            existing = (
                session.query(Model)
                .filter_by(
                    dataset_id=model_data["dataset_id"],
                    config_id=model_data["config_id"],
                    name=model_data["name"],
                )
                .first()
            )
            if existing:
                continue
            session.add(Model(**model_data))

        metrics_data = [
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[0].config_id,
                "train_accuracy": 0.8934,
                "train_loss": 2.7936,
            },
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[1].config_id,
                "train_accuracy": 0.5629,
                "train_loss": 3.2050,
            },
            {
                "dataset_id": dataset.dataset_id,
                "config_id": configs[2].config_id,
                "train_accuracy": 0.9527,
                "train_loss": 1.0045,
            },
        ]

        for metric_data in metrics_data:
            existing = (
                session.query(Metric)
                .filter_by(
                    dataset_id=metric_data["dataset_id"],
                    config_id=metric_data["config_id"],
                )
                .first()
            )
            if existing:
                continue
            session.add(Metric(**metric_data))

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
