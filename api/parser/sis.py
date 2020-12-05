"""
This module provides an interface for web scraping the SIS course search page which
lists ALL course sections for a particular semester.
"""

from enum import Enum
from api.models import CourseSection, CourseSectionPeriod
from typing import Any, Dict, List, Optional, Tuple
import requests
import lxml.html


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
    INSTRUCTOR = 19
    DATE = 20
    LOCATION = 21
    ATTRIBUTE = 22


class SIS:
    LOGIN_URL = "https://cas-auth-ent.rpi.edu/cas/login?service=https://bannerapp04-bnrprd.server.rpi.edu:443/ssomanager/c/SSB"
    START_SEARCH_URL = "https://sis.rpi.edu/rss/bwckgens.p_proc_term_date"
    COURSE_SEARCH_URL = "https://sis.rpi.edu/rss/bwskfcls.P_GetCrse_Advanced"
    DAY_LETTERS = {"M": 1, "T": 2, "W": 3, "R": 4, "F": 5}

    def __init__(self, rin: str, pin: str) -> None:
        self.rin = rin
        self.pin = pin
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

        # Query for all rows in the sections table
        section_rows = tree.xpath(
            "//table[./caption[contains(text(), 'Sections Found')]]//tr"
        )[
            2:
        ]  # Skip first two heading rows

        last_crn = None
        sections = dict()
        for tr in section_rows:
            # Each TD can have different elements in it
            # _extract_td_value will properly determine the string values or return None for empty
            values = list(map(SIS._extract_td_value, tr.xpath("td")))
            period = SIS._create_course_section_period(semester_id, values)

            print(period.json())

            if last_crn is None:
                # First listed section
                pass
            elif values[Column.CRN] is None:
                # Another row for current section
                pass
            else:
                # New section
                sections[values[Column.CRN]] = CourseSection()
                last_crn = values[Column.CRN]

        return sections.values()

    @staticmethod
    def _create_course_section_period(semester_id: str, values) -> CourseSectionPeriod:
        start_time, end_time = SIS._determine_times(values[Column.TIME])

        days = []
        if days is not None:
            days = list(map(lambda letter: SIS.DAY_LETTERS[letter], values[Column.DAYS]))

        return CourseSectionPeriod(
            semester_id=semester_id,
            crn=values[Column.CRN],
            class_type="lecture",
            start_time=start_time,
            end_time=end_time,
            instructors=[values[Column.INSTRUCTOR]] if values[Column.INSTRUCTOR] else [],
            location=values[Column.LOCATION],
            days=days,
        )

    @staticmethod
    def _create_course_section(
        semester_id: str, periods: List[CourseSectionPeriod]
    ) -> CourseSection:
        return CourseSection(
            semester_id=semester_id,
            periods=periods
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

    @staticmethod
    def _sanitize(str: str) -> str:
        """Sanitize a string by stripping whitespace on edges and in between."""
        return " ".join(str.strip().split())

    @staticmethod
    def _extract_td_value(td: Any) -> Optional[str]:
        val = td.xpath("descendant-or-self::*/text()")

        if len(val):
            sanitized = SIS._sanitize("".join(val))
            if sanitized == "" or "TBA" in sanitized:
                return None
            return sanitized
        else:
            return None

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