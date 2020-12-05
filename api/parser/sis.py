"""
This module provides an interface for web scraping the SIS course search page which
lists ALL course sections for a particular semester.
"""

from typing import List
import requests
import lxml.html


class SIS:
    LOGIN_URL = "https://cas-auth-ent.rpi.edu/cas/login?service=https://bannerapp04-bnrprd.server.rpi.edu:443/ssomanager/c/SSB"
    START_SEARCH_URL = 'https://sis.rpi.edu/rss/bwckgens.p_proc_term_date'
    COURSE_SEARCH_URL = "https://sis.rpi.edu/rss/bwskfcls.P_GetCrse_Advanced"

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

    def fetch_semester_subjects(self, semester_id: str) -> List[str]:
        """
        Fetch the subjects listed for a specific semester. Returns the unique, 4-letter codes instead of
        the full names.

        e.g. `['ADMIN', 'USAF', ...]`
        """

        search_page = self.session.post(SIS.START_SEARCH_URL, {
            "p_calling_proc": "P_CrseSearch",
            "p_term": semester_id
        })
        tree = lxml.html.fromstring(search_page.content)
        return tree.xpath("//select[@id='subj_id']/option/@value")

    def fetch_course_sections(self, semester_id: str):
        params = {
            "term_in": semester_id,
            "path": "1",
            "sel_subj": self.fetch_semester_subjects(semester_id),
            "sel_ptrm": ["dummy", "%"],
            "SUB_BTN": "Section Search"
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

        course_sections_page = self.session.get(SIS.COURSE_SEARCH_URL, params=params)

        return course_sections_page