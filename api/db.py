from typing import Any, List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
from pypika.enums import Order
from .models import CourseSection, CourseSectionPeriod

from pypika import Query, Table, Field
from pypika.queries import QueryBuilder

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

COURSE_SECTIONS_TABLE = Table('course_sections')
BASE_COURSE_SECTIONS_QUERY: QueryBuilder = Query.from_(Table('course_sections')).select(
    '*').orderby('course_subject_prefix').orderby('course_number').orderby('section_id')

conn = psycopg2.connect(
    os.environ["POSTGRES_DSN"], cursor_factory=RealDictCursor)


def update_course_sections(semester_id: str, course_sections: List[CourseSection]):
    c = conn.cursor()

    c.execute("DELETE FROM course_section_periods")
    c.execute("DELETE FROM course_sections")
    # # c.execute(
    # #     'UPDATE course_sections SET removed=true WHERE semester_id=%s', (semester_id,))
    # c.execute('SELECT crn FROM course_sections WHERE semester_id=%s',
    #           (semester_id,))

    # existing_crns = c.fetchall()

    for course_section in course_sections:
        record = course_section.to_record()

        # Add new record
        placeholders = ','.join(
            map(lambda key: f'%({key})s', record.keys()))
        c.execute(
            f'INSERT INTO course_sections({",".join(record.keys())}) VALUES ({placeholders})', record)
        print(f'Added new course_section {record["crn"]}')

        # Add course sections
        for period in course_section.periods:
            record = period.to_record()
            placeholders = ','.join(
                map(lambda key: f'%({key})s', record.keys()))
            c.execute(
                f'INSERT INTO course_section_periods({",".join(record.keys())}) VALUES ({placeholders})', record)
            print(
                f'Added {period.class_type} period for {course_section.crn}')
    conn.commit()


def fetch_course_sections(semester_id: str, crns: List[str]) -> CourseSection:
    c = conn.cursor()

    # Create query
    q: QueryBuilder = BASE_COURSE_SECTIONS_QUERY.where(
        COURSE_SECTIONS_TABLE.semester_id == semester_id
    ).where(COURSE_SECTIONS_TABLE.crn.isin(crns))

    c.execute(q.get_sql())

    records = c.fetchall()

    return records_to_sections(semester_id, records)


def search_course_sections(semester_id: str, limit: int, offset: int, **search):
    c = conn.cursor()

    q: QueryBuilder = BASE_COURSE_SECTIONS_QUERY.where(
        COURSE_SECTIONS_TABLE.semester_id == semester_id
    ).limit(limit).offset(offset)

    # Values that require exact matches
    for col in ['course_number', 'course_subject_prefix']:
        if search[col]:
            q = q.where(COURSE_SECTIONS_TABLE[col] == search[col])

    # Values that require wildcards
    for col in ['course_title']:
        if search[col]:
            q = q.where(COURSE_SECTIONS_TABLE[col].ilike(f'%{search[col]}%'))

    # Special values that require complex checks
    if search['has_seats'] == False:
        q = q.where(COURSE_SECTIONS_TABLE.enrollments >=
                    COURSE_SECTIONS_TABLE.max_enrollments)

    if search['has_seats'] == True:
        q = q.where(COURSE_SECTIONS_TABLE.enrollments <
                    COURSE_SECTIONS_TABLE.max_enrollments)

    c.execute(q.get_sql())
    records = c.fetchall()

    return records_to_sections(semester_id, records)


def fetch_course_section_periods(semester_id: str, crn: str) -> List[CourseSectionPeriod]:
    c = conn.cursor()
    c.execute(
        'SELECT * FROM course_section_periods WHERE semester_id=%s and crn=%s', (semester_id, crn))
    course_section_periods_raw = c.fetchall()

    return list(map(CourseSectionPeriod.from_record, course_section_periods_raw))


def fetch_courses(semester_id: str):
    c = conn.cursor()
    c.execute("""
        select
            cs.course_subject_prefix ,
            cs.course_number,
            cs.course_title,
            count(cs.crn) as period_count
        from
            course_sections cs
        where
            cs.semester_id = %s
        group by
            (cs.course_subject_prefix,
            cs.course_number,
            cs.course_title,
            cs.semester_id)
        order by
            cs.course_subject_prefix,
            cs.course_number""", (semester_id,))
    return c.fetchall()


def records_to_sections(semester_id: str, records: List[Dict]) -> List[CourseSection]:
    sections = []
    for record in records:
        periods = fetch_course_section_periods(
            semester_id, record["crn"])

        sections.append(CourseSection.from_record(record, periods))
    return sections
