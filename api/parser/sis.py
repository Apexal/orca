"""
This module provides an interface for web scraping the SIS course search page which
lists ALL course sections for a particular semester.
"""

from enum import Enum
from api.models import CourseSection
from typing import Any, Dict, List, Optional
import requests
import lxml.html


class SIS:
    LOGIN_URL = "https://cas-auth-ent.rpi.edu/cas/login?service=https://bannerapp04-bnrprd.server.rpi.edu:443/ssomanager/c/SSB"
    START_SEARCH_URL = "https://sis.rpi.edu/rss/bwckgens.p_proc_term_date"
    COURSE_SEARCH_URL = "https://sis.rpi.edu/rss/bwskfcls.P_GetCrse_Advanced"

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

        course_sections_page = self.session.get(
            SIS.COURSE_SEARCH_URL,
            params=self._create_search_params(semester_id, subjects),
        )
        # print(course_sections_page.content)
        tree = lxml.html.fromstring(course_sections_page.content)

        # Query for all rows in the sections table
        section_rows = tree.xpath(
            "//table[./caption[contains(text(), 'Sections Found')]]//tr"
        )
        for tr in section_rows:
            tds = tr.xpath("td")
            if len(tds) == 0:
                continue
            # Each TD can have different elements in it
            # _extract_td_value will properly determine the string values or return None for empty
            values = list(map(SIS._extract_td_value, tds))

        return course_sections_page

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