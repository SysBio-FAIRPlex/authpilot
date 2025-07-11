from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class SyntheticDataset(Base):
    __tablename__ = "synthetic_dataset"

    ID = Column(String, primary_key=True)
    dataset = Column(String)
    status = Column(String)
    sex = Column(String)
    age_at_sampling = Column(Integer)
    age_at_death = Column(Integer)
    APOE4_compund_genotype = Column(Integer)
    time_from_baseline = Column(Float)
    repository_link = Column(String)


    def to_dict(self):
        return {
            "ID": self.ID,
            "dataset": self.dataset,
            "status": self.status,
            "sex": self.sex,
            "age_at_sampling": self.age_at_sampling,
            "age_at_death": self.age_at_death,
            "APOE4_compund_genotype": self.APOE4_compund_genotype,
            "time_from_baseline": self.time_from_baseline,
            "repository_link": self.repository_link,
        }


    def to_row(self):
        return [
            self.ID,
            self.dataset,
            self.status,
            self.sex,
            self.age_at_sampling,
            self.age_at_death,
            self.APOE4_compund_genotype,
            self.time_from_baseline,
            self.repository_link,
        ]
