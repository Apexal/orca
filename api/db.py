from typing import Any, List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
from .models import CourseSection, CourseSectionPeriod

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

conn = psycopg2.connect(
    os.environ["POSTGRES_DSN"], cursor_factory=RealDictCursor)


def update_course_sections(semester_id: str, course_sections: List[CourseSection]):
    c = conn.cursor()

    c.execute("DELETE FROM course_section_periods")
    c.execute("DELETE FROM course_sections")
    # c.execute(
    #     'UPDATE course_sections SET removed=true WHERE semester_id=%s', (semester_id,))
    c.execute('SELECT crn FROM course_sections WHERE semester_id=%s',
              (semester_id,))

    existing_crns = c.fetchall()
    print(existing_crns)
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


def _raw_to_course_section_period(raw: Dict[str, Any]) -> CourseSectionPeriod:
    if raw['instructors']:
        raw['instructors'] = raw['instructors'].split('/')
    if raw['days']:
        raw['days'] = list(map(int, raw['days'].split(',')))

    return CourseSectionPeriod(**raw)
