from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    datasets: list["Dataset"] = Relationship(back_populates="owner")

class Dataset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    original_name: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    owner: Optional[User] = Relationship(back_populates="datasets")
    result: Optional["Result"] = Relationship(back_populates="dataset")

class Result(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id", unique=True)
    summary_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    dataset: Optional[Dataset] = Relationship(back_populates="result")
