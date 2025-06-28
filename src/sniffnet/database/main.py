from sniffnet.database.db import engine
from sniffnet.database.db_models import Base

Base.metadata.create_all(bind=engine)