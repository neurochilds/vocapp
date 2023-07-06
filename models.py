from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, create_engine
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True) # creates an index for the username field for faster lookup time
    password_hash: str

    words: List['Word'] = Relationship(back_populates='user')

class Word(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str = Field(index=True) 
    definition: str
    box_number: int
    last_reviewed_date: datetime
    next_review_date: datetime

    user_id: int = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates='words')

sqlite_file_name = "vocapp_database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)
SQLModel.metadata.create_all(engine)