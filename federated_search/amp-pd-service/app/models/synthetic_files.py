from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class SyntheticFiles(Base):
    __tablename__ = "synthetic_files"

    drs_url = Column(String, primary_key=True)
    filename = Column(String)
    filesize_bytes = Column(Integer)
    description = Column(String)


    def to_dict(self):
        return {
            "drs_url": self.drs_url,
            "filename": self.filename,
            "filesize_bytes": self.filesize_bytes,
            "description": self.description,
        }


    def to_row(self):
        return [
            self.drs_url,
            self.filename,
            self.filesize_bytes,
            self.description,
        ]
