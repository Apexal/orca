from typing import List, Optional
from pydantic import BaseModel


class CourseSectionPeriod(BaseModel):
    class_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    instructor: Optional[str] = None
    days: List[int]


class CourseSection(BaseModel):
    subject_prefix: str
    subject_code: str
    title: str
    section_id: str
    crn: str
    intruction_method: Optional[str] = None
    credits: List[int]
    periods: List[CourseSectionPeriod]
    max_enrollments: int
    enrollments: int
    textbooks_url: Optional[str] = ''

    def __str__(self) -> str:
        return f"Course({self.crn}, {self.subject_prefix}-{self.subject_code}, {self.section_id}) -> {len(self.periods)} periods"
