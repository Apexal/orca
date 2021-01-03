from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from pydantic.fields import Field
import datetime

from enum import Enum


class Semester(BaseModel):
    semester_id: str = Field(example="202101")
    title: str = Field(example="Spring 2021")
    start_date: datetime.date
    end_date: datetime.date

    @staticmethod
    def from_record(record: Dict[str, Any]):
        print(record)
        return Semester(
            **record, start_date=record["start_end"].lower, end_date=record["start_end"].upper)


class ClassTypeEnum(str, Enum):
    LECTURE = "lecture"
    STUDIO = "studio"
    RECITATION = "recitation"
    SEMINAR = "seminar"
    LAB = "lab"
    TEST = "test"


class CourseSectionPeriod(BaseModel):
    semester_id: str = Field(example="202101")
    crn: str = Field(example="42608")
    type: Optional[ClassTypeEnum] = Field(None, example=ClassTypeEnum.LECTURE)
    start_time: Optional[str] = Field(
        None,
        description="24-hour 0-padded start time hh:mm format (RPI time)",
        example="14:00",
    )
    end_time: Optional[str] = Field(
        None,
        description="24-hour 0-padded end time hh:mm format (RPI time)",
        example="15:50",
    )
    instructors: List[str] = Field(
        description="Last names of instructor(s)", example=["Hanna", "Shablovsky"]
    )
    location: Optional[str] = Field(
        description="Location of class (null if not yet determined or online)",
        example="SAGE 114",
    )
    days: List[int] = Field(
        description="Days of week period meets (0-Sunday)", example=[1, 4]
    )

    @staticmethod
    def from_record(record: Dict[str, Any]):
        """Creates a CourseSectionPeriod from a DB record."""
        return CourseSectionPeriod(**record)

    def to_record(self) -> Dict[str, Any]:
        """Convert period to flat dictionary to store in DB."""
        return {**self.dict(), }

    def __str__(self) -> str:
        return f"{self.type} on days {self.days} from {self.start_time}-{self.end_time} with {self.instructors} at {self.location}"

    class Config:
        use_enum_values = True


class CourseSection(BaseModel):
    semester_id: str = Field(example="202101")
    course_subject_prefix: str = Field(example="BIOL")
    course_number: str = Field(example="1010")
    course_title: str = Field(example="INTRODUCTION TO BIOLOGY")
    section_id: str = Field(example="01")
    crn: str = Field(example="42608")
    instruction_method: Optional[str] = None
    credits: List[int] = Field(example=[4])
    periods: Optional[List[CourseSectionPeriod]]
    max_enrollments: int = Field(example=150)
    enrollments: int = Field(example=148)
    waitlist_max: int = Field(example=0)
    waitlists: int = Field(
        example=0, description="The number of students on the waitlist.")
    textbooks_url: Optional[str] = None

    @staticmethod
    def from_record(record: Dict[str, Any], periods: Optional[List[CourseSectionPeriod]] = None):
        """Creates a CourseSection from a DB record."""
        record["periods"] = periods

        return CourseSection(**record)

    def to_record(self) -> Dict[str, Any]:
        """Convert period to flat dictionary to store in DB."""
        return self.dict(exclude={"periods"})

    def __str__(self) -> str:
        return f"{self.crn}: {self.course_subject_prefix}-{self.course_number}-{self.section_id} {self.course_title} w/ {len(self.periods)} periods"


class Course(BaseModel):
    semester_id: str = Field(example="202101")
    subject_prefix: str = Field(example="BIOL")
    number: str = Field(example="1010")
    title: str = Field(example="INTRODUCTION TO BIOLOGY")
    sections: Optional[List[CourseSection]] = Field()
