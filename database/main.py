from db import engine
from db_models import Base

Base.metadata.create_all(bind=engine)