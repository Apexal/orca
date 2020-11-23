from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from pydantic.fields import Field


from enum import Enum


class ClassTypeEnum(str, Enum):
    LECTURE = 'lecture'
    STUDIO = 'studio'
    RECITATION = 'recitation'
    SEMINAR = 'seminar'
    LAB = 'lab'
    TEST = 'test'


class CourseSectionPeriod(BaseModel):
    semester_id: str = Field(example="202101")
    crn: str = Field(example="42608")
    class_type: Optional[ClassTypeEnum] = Field(None, example="lecture")
    start_time: Optional[str] = Field(
        None, description="24-hour 0-padded start time hh:mm format (RPI time)", example="14:00")
    end_time: Optional[str] = Field(
        None, description="24-hour 0-padded end time hh:mm format (RPI time)", example="15:50")
    instructors: List[str] = Field(
        description="Last names of instructor(s)", example=["Hanna", "Shablovsky"])
    days: List[int] = Field(
        description="Days of week period meets (0-Sunday", example=[1, 4])

    def to_record(self) -> Dict[str, Any]:
        '''Convert period to flat dictionary to store in DB.'''
        return {
            'semester_id': self.semester_id,
            'crn': self.crn,
            'class_type': self.class_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'instructors': '/'.join(self.instructors),
            'days': ','.join(map(str, self.days))
        }


class CourseSection(BaseModel):
    semester_id: str = Field(example="202101")
    course_subject_prefix: str = Field(example="BIOL")
    course_number: str = Field(example="1010")
    course_title: str = Field(example="INTRODUCTION TO BIOLOGY")
    section_id: str = Field(example="01")
    crn: str = Field(example="42608")
    intruction_method: Optional[str] = None
    credits: List[int] = Field(example=[4])
    periods: List[CourseSectionPeriod]
    max_enrollments: int = Field(example=150)
    enrollments: int = Field(example=148)
    textbooks_url: Optional[str] = None

    def to_record(self) -> Dict[str, Any]:
        '''Convert period to flat dictionary to store in DB.'''
        return {
            'semester_id': self.semester_id,
            'course_subject_prefix': self.course_subject_prefix,
            'course_number': self.course_number,
            'course_title': self.course_title,
            'crn': self.crn,
            'section_id': self.section_id,
            'instruction_method': self.intruction_method,
            'credits': ','.join(map(str, self.credits)),
            'max_enrollments': self.max_enrollments,
            'enrollments': self.enrollments,
            'textbooks_url': self.textbooks_url
        }

    def __str__(self) -> str:
        return f"{self.crn}: {self.course_subject_prefix}-{self.course_code}-{self.section_id} {self.course_title} w/ {len(self.periods)} periods"
