"""
This module provides an interface for web scraping the SIS course search page which
lists ALL course sections for a particular semester.
"""

from api.parser import DAY_LETTERS
from api.parser.utils import extract_td_value, sanitize
from enum import Enum
from api.models import ClassTypeEnum, CourseSection, CourseSectionPeriod
from typing import Any, Dict, List, Optional, Tuple
import requests
import lxml.html
from lxml import etree


class Column:
    CRN = 1
    SUBJECT = 2
    CRSE = 3
    SECTION = 4
    CAMPUS = 5
    CREDITS = 6
    TITLE = 7
    DAYS = 8
    TIME = 9
    CAP = 10
    ACTUAL = 11
    WL_CAP = 12
    WL_ACTUAL = 13
    INSTRUCTOR = 19
    DATE = 20
    LOCATION = 21
    ATTRIBUTE = 22


class SIS:
    LOGIN_URL = "https://cas-auth-ent.rpi.edu/cas/login?service=https://bannerapp04-bnrprd.server.rpi.edu:443/ssomanager/c/SSB"
    START_SEARCH_URL = "https://sis.rpi.edu/rss/bwckgens.p_proc_term_date"
    COURSE_SEARCH_URL = "https://sis.rpi.edu/rss/bwskfcls.P_GetCrse_Advanced"

    def __init__(
        self,
        rin: str,
        pin: str,
        period_types: Optional[Dict[Tuple[str, int, str], ClassTypeEnum]] = None,
    ) -> None:
        self.rin = rin
        self.pin = pin
        self.period_types = period_types if period_types is not None else dict()
        self.session = requests.Session()  # Persistent session to make requests

    def login(self) -> bool:
        """
        Attempts to login to SIS with the provided RIN and PIN. Returns True/False based on success.
        False most likely means the provided credentials were incorrect.
        """

        # Cannot make POST request directly, need CSRF token in hidden form input first
        login_page = self.session.get(SIS.LOGIN_URL)
        tree = lxml.html.fromstring(login_page.content)

        csrf_token = tree.xpath('//input[@name = "execution"]/@value')[0]
        response = self.session.post(
            SIS.LOGIN_URL,
            {
                "username": self.rin,
                "password": self.pin,
                "_eventId": "submit",
                "execution": csrf_token,
            },
        )
        return "Rensselaer Self-Service Information System" in response.text

    def fetch_subjects(self, semester_id: str) -> List[str]:
        """
        Fetch the subjects listed for a specific semester. Returns the unique, 4-letter codes instead of
        the full names.

        e.g. `['ADMIN', 'USAF', ...]`
        """

        search_page = self.session.post(
            SIS.START_SEARCH_URL,
            {"p_calling_proc": "P_CrseSearch", "p_term": semester_id},
        )
        tree = lxml.html.fromstring(search_page.content)
        return tree.xpath("//select[@id='subj_id']/option/@value")

    def fetch_course_sections(
        self, semester_id: str, subjects: List[str] = None
    ) -> List[CourseSection]:

        if subjects is None:
            subjects = self.fetch_subjects(semester_id)

        # Submit search page and parse document
        course_sections_page = self.session.get(
            SIS.COURSE_SEARCH_URL,
            params=self._create_search_params(semester_id, subjects),
        )
        tree = lxml.html.fromstring(course_sections_page.content)

        # Query for all rows in the sections table, Skip first two heading rows
        section_rows = tree.xpath(
            "//table[./caption[contains(text(), 'Sections Found')]]//tr"
        )[2:]

        last_crn = "start"
        sections = dict()
        for tr in section_rows:
            # Each TD can have different elements in it
            # extract_td_value will properly determine the string values or return None for empty
            tds = tr.xpath("td")
            if len(tds) == 0:
                continue
            # Add empty values since SIS doesn't create a TD for them
            i = 0
            while i < len(tds):
                if tds[i].xpath("@colspan"):
                    # Need to add another empty td
                    tds.insert(i + 1, etree.Element("td"))
                i += 1
            values = list(map(extract_td_value, tds))

            if values[Column.CRN] is not None and values[Column.CRN] != last_crn:
                # New section
                sections[values[Column.CRN]] = SIS._create_course_section(
                    semester_id, values
                )
                last_crn = values[Column.CRN]

            period = SIS._create_course_section_period(semester_id, last_crn, values, self.period_types)
            sections[last_crn].periods.append(period)

        return list(sections.values())

    @staticmethod
    def _create_course_section_period(
        semester_id: str,
        crn: str,
        values: List[Optional[str]],
        period_types: Dict[Tuple[str, int, str], ClassTypeEnum],
    ) -> CourseSectionPeriod:
        start_time, end_time = SIS._determine_times(values[Column.TIME])

        days = []
        if values[Column.DAYS] is not None:
            days = list(map(lambda letter: DAY_LETTERS[letter], values[Column.DAYS]))

        instructors = []
        if values[Column.INSTRUCTOR] is not None:
            instructors = values[Column.INSTRUCTOR].replace(" (P)", "").split(", ")

        period_type = "lecture"
        if len(days) > 0:
            period_type_key = (crn, days[0], start_time)
            if period_type_key in period_types:
                period_type = period_types[(crn, days[0], start_time)]

        return CourseSectionPeriod(
            semester_id=semester_id,
            crn=crn,
            type=period_type,
            start_time=start_time,
            end_time=end_time,
            instructors=instructors,
            location=values[Column.LOCATION],
            days=days,
        )

    @staticmethod
    def _create_course_section(semester_id: str, values: Dict) -> CourseSection:
        if "-" in values[Column.CREDITS]:
            min_credits, max_credits = map(
                int, map(float, values[Column.CREDITS].split("-"))
            )
            credits = list(range(min_credits, max_credits + 1))
        else:
            credits = [int(float(values[Column.CREDITS]))]

        return CourseSection(
            semester_id=semester_id,
            course_subject_prefix=values[Column.SUBJECT],
            course_number=values[Column.CRSE],
            course_title=values[Column.TITLE],
            section_id=values[Column.SECTION],
            crn=values[Column.CRN],
            instruction_method=values[Column.ATTRIBUTE],
            credits=credits,
            max_enrollments=int(values[Column.CAP]),
            enrollments=int(values[Column.ACTUAL]),
            waitlist_max=int(values[Column.WL_CAP]),
            waitlists=int(values[Column.WL_ACTUAL]),
            periods=[],
        )

    @staticmethod
    def _to_24_hour_time(time: str) -> str:
        hours, minutes = map(int, time.replace("am", "").replace("pm", "").split(":"))

        if hours == 12 and "am" in time:
            hours = 0
        elif "pm" in time and hours != 12:
            hours += 12
        return f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}"

    @staticmethod
    def _determine_times(times: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if times is None:
            return (None, None)

        # times = "10:10 am-12:00 pm"
        # "10:10 am", "12:00 pm"
        return tuple(map(SIS._to_24_hour_time, times.split("-")))

    def _create_search_params(
        self, semester_id: str, subjects: List[str]
    ) -> Dict[str, str]:
        params = {
            "term_in": semester_id,
            "path": "1",
            "sel_subj": ["dummy"] + subjects,
            "sel_ptrm": ["dummy", "%"],
            "SUB_BTN": "Section Search",
        }

        # All of these keys NEED to be present or SIS cries like a baby.
        # Instead of typing these manually, here we map values to the search keys
        # and automatically fill `params` from this
        #
        # side note: wth is SIS doing that it requires 'dummy' as an empty value separate from ''
        fill_params = {
            "dummy": [
                "rsts",
                "crn",
                "sel_day",
                "sel_schd",
                "sel_insm",
                "sel_camp",
                "sel_levl",
                "sel_sess",
                "sel_instr",
                "sel_attr",
            ],
            "": ["sel_crse", "sel_title", "sel_from_cred", "sel_to_cred"],
            "0": ["begin_hh", "begin_mi", "end_hh", "end_mi"],
            "a": ["begin_ap", "end_ap"],
        }
        for value, keys in fill_params.items():
            for key in keys:
                params[key] = value

        return params
