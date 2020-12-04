from pydantic.types import constr
from api.models import Course, CourseSection
from .parse import parse
from .db import fetch_course_sections, fetch_courses_with_sections, fetch_courses_without_sections, search_course_sections, update_course_sections
from typing import List, Optional

from fastapi import FastAPI
from fastapi.params import Path, Query
from fastapi.middleware.cors import CORSMiddleware

with open('README.md') as f:
    description = f.read()

# Initialize FastAPI
app = FastAPI(
    title='Open-source RPI Course API',
    description=description,
    version='0.1.1'
)

# Allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

CRN = constr(regex="^[0-9]{5}$")
'''A constrained string that must be a 5 digit number. All CRNs conform to this (I think).'''


@app.get('/{semester_id}/sections/update', tags=['sections'])
async def update_sections(semester_id: str):
    course_sections = parse(semester_id)
    update_course_sections(semester_id, course_sections)
    return 'Updated'


@app.get("/{semester_id}/sections",
         tags=["sections"],
         response_model=List[CourseSection],
         response_description="The paginated list of course sections that match the queries.",
         summary="Fetch/search course periods")
async def get_sections(
        semester_id: str = Path(None,
                                example='202101', description="The id of the semester, determined by the Registrar."),
        crns: Optional[List[CRN]] = Query(
            None, description="The direct CRNs of the course sections to fetch. If present, no other search parameters can be set and `limit` and `offset` are ignored.", example=["42608"]),
        course_subject_prefix: Optional[str] = Query(None),
        course_number: Optional[str] = Query(None),
        course_title: Optional[str] = Query(None),
        has_seats: Optional[bool] = Query(None),
        limit: int = Query(
            100, description="The maximum number of course sections to return in the response."),
        offset: int = Query(0, description="The number of course sections in the response to skip.")):
    """
    Directly fetch course sections by CRN or search with different query parameters. Always returns a paginated response.
    """
    sections = []

    # Determine which filters to apply
    if crns:
        # If CRNs are given, no other search queries should be passed
        sections = fetch_course_sections(semester_id, crns)
    else:
        sections = search_course_sections(
            semester_id,
            limit,
            offset,
            course_subject_prefix=course_subject_prefix,
            course_number=course_number,
            course_title=course_title,
            has_seats=has_seats)
    return sections


@app.get("/{semester_id}/courses", tags=["courses"], summary="Fetch/search courses", response_model=List[Course])
async def get_courses(semester_id: str = Path(None,
                                              example='202101', description="The id of the semester, determined by the Registrar."),
                      include_sections: bool = Query(True),
                      title: Optional[str] = Query(None),
                      subject_prefix: Optional[str] = Query(None),
                      number: Optional[str] = Query(None),
                      limit: int = Query(
    100, description="The maximum number of course sections to return in the response."),
    offset: int = Query(
    0, description="The number of course sections in the response to skip."
)
):
    if include_sections:
        return fetch_courses_with_sections(semester_id, limit, offset)
    else:
        courses = fetch_courses_without_sections(semester_id, limit, offset)
        return courses
