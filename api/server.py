from api.parser.registrar import Registrar
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
from pydantic.types import constr
from api.models import Course, CourseSection
from .parser.sis import SIS
from .db import (
    fetch_course_sections, fetch_course_subject_prefixes,
    fetch_courses_without_sections, populate_course_periods,
    search_course_sections,
    update_course_sections,
)
from typing import List, Optional
from api import api_version

from fastapi import FastAPI, HTTPException
from fastapi.params import Path, Query
from fastapi.middleware.cors import CORSMiddleware

with open("README.md") as f:
    description = f.read()

# Initialize FastAPI
app = FastAPI(
    title="Open-source RPI Course API", description=description, version=api_version
)

# Allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CRN = constr(regex="^[0-9]{5}$")
"""A constrained string that must be a 5 digit number. All CRNs conform to this (I think)."""


@app.get(
    "/{semester_id}/sections",
    tags=["sections"],
    response_model=List[CourseSection],
    response_description="The paginated list of course sections that match the queries.",
    summary="Fetch/search course periods",
)
async def get_sections(
    semester_id: str = Path(
        None,
        example="202101",
        description="The id of the semester, determined by the Registrar.",
    ),
    crns: Optional[List[CRN]] = Query(
        None,
        description="The direct CRNs of the course sections to fetch. If present, no other search parameters can be set and `limit` and `offset` are ignored.",
        example=["42608"],
    ),
    course_subject_prefix: Optional[str] = Query(None),
    course_number: Optional[str] = Query(None),
    course_title: Optional[str] = Query(None),
    days: Optional[List[str]] = Query(None, title="Meeting days", description="`NOT YET IMPLEMENTED`"),
    has_seats: Optional[bool] = Query(None, title="Has open seats"),
    limit: int = Query(
        10,
        description="The maximum number of course sections to return in the response. Max: 50",
        gt=0,
        lt=51,
    ),
    offset: int = Query(
        0, description="The number of course sections in the response to skip."
    ),
):
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
            has_seats=has_seats,
        )
    return sections


@app.get(
    "/{semester_id}/courses",
    tags=["courses"],
    summary="Fetch/search courses",
    response_model=List[Course],
)
async def get_courses(
    semester_id: str = Path(
        None,
        example="202101",
        description="The id of the semester, determined by the Registrar.",
    ),
    include_sections: bool = Query(False, description="Populate `sections` for each course."),
    include_periods: bool = Query(True, description="`NOT YET IMPLEMENTED` Populate `periods` of each section (only checked if `include_sections` is True)"),
    title: Optional[str] = Query(None, description="`NOT YET IMPLEMENTED`"),
    days: Optional[List[str]] = Query(None, description="`NOT YET IMPLEMENTED`"),
    subject_prefix: Optional[str] = Query(None, description="`NOT YET IMPLEMENTED`"),
    number: Optional[str] = Query(None, description="`NOT YET IMPLEMENTED`"),
    limit: int = Query(
        10,
        description="The maximum number of course sections to return in the response. Max: 50",
        gt=0,
        lt=51,
    ),
    offset: int = Query(
        0, description="The number of course sections in the response to skip."
    ),
):
    courses = fetch_courses_without_sections(semester_id, limit, offset)

    if include_sections:
        populate_course_periods(semester_id, courses, include_sections)

    return courses

@app.get("/{semester_id}/courses/subjects", tags=["courses"], summary="Fetch course subject prefixes", response_model=List[str])
async def list_course_subject_prefixes():
    """Fetch the unique course subject prefixes: e.g. BIOL, CSCI, ESCI, MATH, etc."""
    return fetch_course_subject_prefixes()

@app.post("/{semester_id}/sections/update", tags=["admin"])
async def update_sections(semester_id: str, api_key: str):
    """
    **ADMIN ONLY**
    Update a semester's data by fetching it from all of the sources. This is called periodically to keep data fresh.
    """
    if api_key != os.environ["API_KEY"]:
        return HTTPException(401, "Invalid API Key! Only admins can do this.")

    period_types = Registrar.parse_period_types(semester_id)
    sis = SIS(os.environ["SIS_RIN"], os.environ["SIS_PIN"], period_types)
    sis.login()
    course_sections = sis.fetch_course_sections(semester_id)
    update_course_sections(semester_id, course_sections)
    return {"update_count": len(course_sections)}
