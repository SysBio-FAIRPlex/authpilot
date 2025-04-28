from sqlalchemy import Column, Integer, String
from app.database import Base

class Person(Base):
    __tablename__ = "person"

    person_id = Column(Integer, primary_key=True)
    gender = Column(String)
    year_of_birth = Column(Integer)
    race = Column(String)
    ethnicity = Column(String)
    diagnosis_name = Column(String)


    def to_dict(self):
        return {
            "person_id": self.person_id,
            "gender": self.gender,
            "year_of_birth": self.year_of_birth,
            "race": self.race,
            "ethnicity": self.ethnicity,
            "diagnosis_name": self.diagnosis_name,
        }


    def to_row(self):
        return [
            self.person_id,
            self.gender,
            self.year_of_birth,
            self.race,
            self.ethnicity,
            self.diagnosis_name,
        ]
