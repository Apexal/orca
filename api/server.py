from pydantic.types import constr
from api.models import CourseSection
from .parse import parse
from .db import fetch_course_sections, search_course_sections, update_course_sections
from typing import List, Optional

from fastapi import FastAPI
from fastapi.params import Path, Query
from fastapi.middleware.cors import CORSMiddleware

description = """
### **ORCA** is an open-source API for querying the Registrar's semesterly course listings.

## Overview
ORCA gives you access to every course offered in a semester along with the sections scheduled with weekly periods. This includes:
- course title
- course id (e.g. BIOL-1010)
- course sections with
    - crn
    - id (section 01, 02, ...)
    - how many credits it can be taken for
    - current enrollment count
    - max enrollment count
    - url to textbooks (RPI Bookstore)
    - section periods with
        - type (lecture, recitation, lab, ...)
        - start and end time
        - days of the week it meets
        - instructor(s)
        - location

Look at the requests' example responses to see the full schemas.

### Data
ORCA periodically fetches its data from the SIS page listing course sections with enrollment data in table format. [Spring 2021 Example](https://sis.rpi.edu/reg/zs202101.htm)
The page is extremely difficult to read and is even difficult to programmatically parse. These pages are fetched every **30 minutes** each day, though it is unclear how often the Registrar updates the pages themselves.

### Uses
This course data can be used for a variety of purposes small and large. Here are some examples:
- create your own scheduling interface (e.g. YACS or QuACS)
- create student tools that use course data
    - used textbook marketplace
    - study group organizers
    - schedule visualizers
    - schedule importers
- data visualizations
    - map out locations of periods
    - create directions for getting to and from classes

### Documentation

#### Semesters
The Registrar evidently identifies semesters with a short numeric code comprising:
1. 4-digit year the semester starts during
2. 2-digit zero padded month the semester starts during
3. (Arch) 2-digit code for specific part of semester
    - `01` - Full Term
    - `02` - First Half
    - `03` - Seond Half

**Examples**
- `20210` Spring 2021
- `202009` Fall 2020
- `20210501` Summer 2021 (Full Term)

#### Database Schema
[Here](https://dbdiagram.io/d/5fbb43a63a78976d7b7cfb03) is a visualization of the simple database schema used for the API. It also has the schema written in Database Markup Language.


#### Source Code
ORCA is entirely open source and hosted on GitHub at [Apexa/orca](https://github.com/Apexal/orca)

### Issues/Feature Requests

Please report these on the GitHub repo at [Apexa/orca](https://github.com/Apexal/orca/issues)!

"""

# Initialize FastAPI
app = FastAPI(
    title='Open-source RPI Course API',
    description=description,
    version='0.1.0'
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
         response_model=List[Optional[CourseSection]],
         response_description="The paginated list of course sections that match the queries.",
         summary="Fetch course periods")
async def get_sections(
        semester_id: str = Path(None,
                                example='202101', description="The id of the semester, determined by the Registrar. Comprises the 4-digit starting year and 2-digit starting month of a semester and then <b>if Summer</b> a 2-digit indicator of which section. e.g. <ul><li><code>202101</code> - Spring 2021</li><li><code>202109</code> - Fall 2021</li><li><code>20210501</code> - Summer Full Term</li></ul>"),
        crns: Optional[List[CRN]] = Query(
            None, description="The direct CRNs of the course sections to fetch. If present, no other search parameters can be set and `limit` and `offset` are ignored.", example=["42608"]),
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
    return sections
