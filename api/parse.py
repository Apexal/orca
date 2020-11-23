from .models import ClassTypeEnum, CourseSection, CourseSectionPeriod
from typing import List, Optional
from datetime import date, datetime
import lxml.html
import re

url = "202101.html"

doc = lxml.html.parse(url)

rows = doc.xpath('//tr[@align = "LEFT"]')

day_letters = {
    "M": 1,
    "T": 2,
    "W": 3,
    "R": 4,
    "F": 5
}

class_types = {
    'SEM': ClassTypeEnum.SEMINAR,
    'TES': ClassTypeEnum.TEST,
    'LEC': ClassTypeEnum.LECTURE,
    'REC': ClassTypeEnum.RECITATION,
    'LAB': ClassTypeEnum.LAB,
    'STU': ClassTypeEnum.STUDIO
}


def sanitize(str: str) -> str:
    '''Sanitize a string by stripping whitespace on edges and in between.'''
    # TODO: strip middle whitespace
    return ' '.join(str.strip().split())


def create_period(semester_id: str, crn: str, values: List[str]) -> CourseSectionPeriod:
    days_raw = values[6]
    days = []
    if days_raw:
        days = list(map(lambda day_letter: day_letters[day_letter], filter(
            lambda v: v != " ", days_raw)))

    return CourseSectionPeriod(
        crn=crn,
        semester_id=semester_id,
        class_type=class_types[values[2]] if values[2] else None,
        start_time='hh:mm a',
        end_time='hh:mm a',
        instructors=values[9].split('/'),
        days=days
    )


def create_course_section(semester_id: str, period_rows: List[List]) -> CourseSection:
    first_row = period_rows[0]
    crn, subject_prefix, subject_code, section_id = re.split(
        ' |-', first_row[0])
    _, title, _, instruction_method, credits_raw, _, _, _, _, _, max_enrollments, enrollments, _, textbook_url = first_row

    credits = []
    if "-" in credits_raw:
        min_credits, max_credits = credits_raw.split("-")
        credits = list(range(int(min_credits), int(max_credits)+1))
    else:
        credits = [int(credits_raw)]

    course = CourseSection(semester_id=semester_id, course_subject_prefix=subject_prefix, course_number=subject_code,
                           course_title=title, section_id=section_id, crn=crn, instruction_method=instruction_method, credits=credits, periods=[create_period(semester_id, crn, period_row) for period_row in period_rows], max_enrollments=max_enrollments, enrollments=enrollments, textbook_url=textbook_url)
    return course


last_parsed = datetime.now()


def parse(semester_id: str) -> List[CourseSection]:
    # if datetime.now() - last_parsed > 100:

    course_sections = []
    last_id = None
    period_rows = []
    for row in rows:
        def extract(index: int) -> Optional[str]:
            '''Extract a specific TD's text or None if empty.'''
            values = row.xpath(f"td[{index}]//span/text()")
            if len(values) == 0:
                return None
            elif "TBA" in values[0]:
                return None
            else:
                return sanitize(values[0])

        all_values = [extract(i) for i in range(1, 15)]

        if all([val is None for val in all_values]):
            if len(period_rows) > 0:
                course_sections.append(
                    create_course_section(semester_id, period_rows))

            period_rows = []
            continue

        # CRN Course-Section
        # e.g. 44854 ARCH-4100-01
        id = extract(1)

        if id is None:
            if last_id is None:
                # print("skipping", id)
                # Haven't reached the first section row yet!
                continue

            # Skip "NOTE:" rows
            if all_values[1]:
                continue

            # More periods
            period_rows.append(all_values)
        else:
            '''Start of new section rows'''

            last_id = id
            if len(period_rows) > 0:
                course_sections.append(
                    create_course_section(semester_id, period_rows))
            period_rows = [all_values]
    if len(period_rows) > 0:
        course_sections.append(create_course_section(semester_id, period_rows))

    return course_sections
