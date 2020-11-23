from typing import List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
from .models import CourseSection, CourseSectionPeriod

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

conn = psycopg2.connect(
    os.environ["POSTGRES_DSN"], cursor_factory=RealDictCursor)


def fetch_course_section(semester_id: str, crn: str) -> CourseSection:
    c = conn.cursor()
    c.execute(
        'SELECT * FROM course_sections WHERE semester_id=%s AND crn=%s', (semester_id, crn))
    course_section_raw = c.fetchone()

    if course_section_raw is None:
        return None

    course_section_raw['periods'] = fetch_course_section_periods(
        semester_id, crn)

    if course_section_raw['credits']:
        course_section_raw['credits'] = list(
            map(int, course_section_raw["credits"].split(",")))

    return CourseSection(
        **course_section_raw)


def fetch_course_section_periods(semester_id: str, crn: str) -> List[CourseSectionPeriod]:
    c = conn.cursor()
    c.execute(
        'SELECT * FROM course_section_periods WHERE semester_id=%s and crn=%s', (semester_id, crn))
    course_section_periods_raw = c.fetchall()

    return list(map(_raw_to_course_section_period, course_section_periods_raw))


def _raw_to_course_section_period(raw: Dict[str, any]) -> CourseSectionPeriod:
    if raw['instructors']:
        raw['instructors'] = raw['instructors'].split('/')
    if raw['days']:
        raw['days'] = list(map(int, raw['days'].split(',')))

    return CourseSectionPeriod(**raw)
