import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, JSON, Integer, String
from geoalchemy2 import Geometry
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


engine = create_engine(
    f'postgresql://postgres:{os.environ["POSTGRES_PASS"]}@localhost:5432/{os.environ["POSTGRES_DB"].strip()}')
Session = sessionmaker(engine)
Base = declarative_base()


class GisPolygon(Base):
    __tablename__ = 'gis_polygon'
    _created = Column(DateTime(timezone=False))
    _updated = Column(DateTime(timezone=False))
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer)
    name = Column(String)
    props = Column(JSON)
    geom = Column(Geometry('POLYGON'))

    def __repr__(self):
        return self.name
