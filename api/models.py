from typing import List, Optional
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
    class_type: Optional[ClassTypeEnum] = Field(None, example="lecture")
    start_time: Optional[str] = Field(
        None, description="24-hour 0-padded start time hh:mm format (RPI time)", example="14:00")
    end_time: Optional[str] = Field(
        None, description="24-hour 0-padded end time hh:mm format (RPI time)", example="15:50")
    instructors: List[str] = Field(
        description="Last names of instructor(s)", example=["Hanna", "Shablovsky"])
    days: List[int] = Field(
        description="Days of week period meets (0-Sunday", example=[1, 4])


class CourseSection(BaseModel):
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

    def __str__(self) -> str:
        return f"Course({self.crn}, {self.course_subject_prefix}-{self.course_code}, {self.section_id}) -> {len(self.periods)} periods"
