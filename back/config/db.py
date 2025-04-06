from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("mysql+pymysql://irilea:HammerKlavier!2023!2023@localhost:3306/dinamico")

meta = MetaData()

conn = engine.connect()

Base = declarative_base(metadata=meta)

Session = sessionmaker(bind=engine, autoflush=True)
sess = Session()
