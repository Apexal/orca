from api.security import API_KEY_QUERY
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Path, Query
from fastapi import FastAPI, HTTPException, Depends
from api import api_version
from typing import List, Optional
from .db import (
    fetch_course_sections, fetch_course_subject_prefixes,
    fetch_courses_without_sections, fetch_semesters, populate_course_periods,
    search_course_sections,
    update_course_sections,
    postgres_pool
)
from .parser.sis import SIS
from api.models import Course, CourseSection, Semester
from pydantic.types import constr
from api.parser.registrar import Registrar
import os
from psycopg2.extras import RealDictConnection


with open("README.md") as f:
    description = f.read()

# Initialize FastAPI
app = FastAPI(
    title="Open-source RPI Course API", description=description, version=api_version
)


@app.on_event("startup")
def on_startup():
    postgres_pool.init()

# Cleanup database connections when FastAPI shutsdown


@app.on_event("shutdown")
def on_shutdown():
    postgres_pool.cleanup()


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


@app.get("/semesters", tags=["semesters"], response_model=List[Semester], summary="Fetch supported semesters", response_description="Semesters which have their schedules loaded into the API.")
async def get_semesters(conn: RealDictConnection = Depends(postgres_pool.get_conn)):
    return fetch_semesters(conn)


@app.get("/{semester_id}/sections", tags=["sections"], response_model=List[CourseSection], summary="Get sections from CRNs", response_description="List of found course sections. Excludes CRNs not found.")
async def get_sections(
    semester_id: str = Path(
        None,
        example="202101",
        description="The id of the semester, determined by the Registrar.",
    ),
    crns: List[CRN] = Query(
        ...,
        description="The direct CRNs of the course sections to fetch.",
        example=["42608"],
    ),
    conn: RealDictConnection = Depends(postgres_pool.get_conn)
):
    """Directly fetch course sections from CRNs."""
    return fetch_course_sections(conn, semester_id, crns)


@app.get(
    "/{semester_id}/sections/search",
    tags=["sections"],
    response_model=List[CourseSection],
    response_description="The paginated list of course sections that match the queries.",
    summary="Search course periods",
)
async def search_sections(
    semester_id: str = Path(
        None,
        example="202101",
        description="The id of the semester, determined by the Registrar.",
    ),
    course_subject_prefix: Optional[str] = Query(None),
    course_number: Optional[str] = Query(None),
    course_title: Optional[str] = Query(None),
    days: Optional[List[str]] = Query(
        None, title="Meeting days", description="`NOT YET IMPLEMENTED`"),
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
    conn: RealDictConnection = Depends(postgres_pool.get_conn)
):
    """
    Search course sections with different query parameters. Always returns a paginated response.
    """

    return search_course_sections(
        conn,
        semester_id,
        limit,
        offset,
        course_subject_prefix=course_subject_prefix,
        course_number=course_number,
        course_title=course_title,
        has_seats=has_seats,
    )


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
    include_sections: bool = Query(
        False, description="Populate `sections` for each course."),
    include_periods: bool = Query(
        True, description="`NOT YET IMPLEMENTED` Populate `periods` of each section (only checked if `include_sections` is True)"),
    title: Optional[str] = Query(None, description="`NOT YET IMPLEMENTED`"),
    days: Optional[List[str]] = Query(
        None, description="`NOT YET IMPLEMENTED`"),
    subject_prefix: Optional[str] = Query(
        None, description="`NOT YET IMPLEMENTED`"),
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
    conn: RealDictConnection = Depends(postgres_pool.get_conn)
):
    courses = fetch_courses_without_sections(conn, semester_id, limit, offset)

    if include_sections:
        populate_course_periods(conn, semester_id, courses, include_sections)

    return courses


@app.get("/{semester_id}/courses/subjects", tags=["courses"], summary="Fetch course subject prefixes", response_model=List[str])
async def list_course_subject_prefixes(conn: RealDictConnection = Depends(postgres_pool.get_conn)):
    """Fetch the unique course subject prefixes: e.g. BIOL, CSCI, ESCI, MATH, etc."""
    return fetch_course_subject_prefixes(conn)
