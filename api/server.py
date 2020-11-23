from pydantic.types import constr
from api.models import CourseSection
from .parse import parse
from .db import fetch_course_section, update_course_sections
from typing import List, Optional

from fastapi import FastAPI
from fastapi.params import Path, Query


# Initialize FastAPI
app = FastAPI(
    title='Open-source RPI Course API',
    description='ORCA is an API for querying the Registrar\'s semesterly course listings.',
    version='0.1.0'
)

CRN = constr(regex="^[0-9]{5}$")
'''A constrained string that must be a 5 digit number. All CRNs conform to this (I think).'''


@app.get('/{semester_id}/sections/update', tags=['sections'])
async def update_sections(semester_id: str):
    course_sections = parse(semester_id)
    update_course_sections(semester_id, course_sections)
    return 'Good!'


@app.get("/{semester_id}/sections",
         tags=["sections"],
         response_model=List[Optional[CourseSection]],
         response_description="The paginated list of course sections that match the queries.",
         summary="Fetch course periods")
async def get_sections(
        semester_id: str = Path(None,
                                example='202101', description="The id of the semester, determined by the Registrar. Comprises the 4-digit starting year and 2-digit starting month of a semester and then <b>if Summer</b> a 2-digit indicator of which section. e.g. <ul><li><code>202101</code> - Spring 2021</li><li><code>202109</code> - Fall 2021</li><li><code>20210501</code> - Summer Full Term</li></ul>"),
        crns: Optional[List[CRN]] = Query(
            None, description="The direct CRNs of the course sections to fetch. If present, no other query parameters can be set.", example=["42608"]),
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
        sections = list(
            map(lambda crn: fetch_course_section(semester_id, crn), crns))[offset:offset+limit]
    return sections
