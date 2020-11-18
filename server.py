from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Course(BaseModel):
    semester: str
    title: str
    subject_prefix: str
    code: str
    description: str
    when_offered: str


class CourseSection(BaseModel):
    section: str
    crn: str


class CourseSectionPeriod(BaseModel):
    type: str
    credits: List[int]
    start_time: Optional[str]
    end_time: Optional[str]
    days: List[int]
    intruction_method: Optional[str] = None
    instructor: str
    max_enrollments: int
    enrollments: int
    textbooks_url: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}
