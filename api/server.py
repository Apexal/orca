from api.parse import parse
from typing import List, Optional

from fastapi import FastAPI
from fastapi.params import Query


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/{semester}/sections/")
async def get_sections(semester: str, crns: List[str] = Query([], max_length=200)):
    course_sections = parse()
    return list(filter(lambda course_section: course_section.crn in crns, course_sections))
