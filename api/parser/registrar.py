from api.parser import DAY_LETTERS, PERIOD_TYPES
from api.parser.utils import extract_td_value
from typing import Dict, List, Tuple
import re
import lxml.html

import requests


class Column:
    CRN_COURSE_SEC = 0
    TITLE = 1
    TYPE = 2
    INSTRUCTION_METHOD = 3
    CREDITS = 4
    DAYS = 6
    START_TIME = 7
    END_TIME = 8
    INSTRUCTOR = 9


class Registrar:
    """
    Web scraper for crappy registrar HTML table page. The ONLY reason to look at this page is that it has
    period types where SIS does not.
    """

    BASE_URL = "https://sis.rpi.edu/reg/zs"

    @staticmethod
    def parse_period_types(
        semester_id: str,
    ) -> Dict[Tuple[str, str, str, str, str, str, str], str]:
        """
        Downloads and parses schedule page for a specific semester.
        Returns a mapping between (43895, W, 12:00) -> lecture
        """

        print("Downloading schedule page... ", end="", flush=True)
        page = requests.get(Registrar.BASE_URL + semester_id + ".htm")
        doc = lxml.html.fromstring(page.content)
        print("Done.")
        rows = doc.xpath('//tr[@align = "LEFT"]')

        period_types = dict()
        last_crn = None
        for row in rows:
            # period_types[(crn, day, start_time)] = period type
            tds = row.xpath("td")
            try:
                crn_course_sec = extract_td_value(tds[Column.CRN_COURSE_SEC])
            except IndexError:
                continue

            if crn_course_sec is None:
                crn = last_crn
            else:
                crn = re.split("-| ", crn_course_sec)[0]

            if crn is None or extract_td_value(tds[1]) == "NOTE:":
                continue

            start_time_raw, end_time_raw = (
                extract_td_value(tds[Column.START_TIME]),
                extract_td_value(tds[Column.END_TIME]),
            )
            start_time, end_time = Registrar.determine_times(
                start_time_raw, end_time_raw
            )
            days = Registrar.determine_days(extract_td_value(tds[Column.DAYS]))
            period_type = extract_td_value(tds[Column.TYPE])
            if period_type:
                for day in days:
                    period_types[(crn, day, start_time)] = PERIOD_TYPES[period_type]

            last_crn = crn

        return period_types

    @staticmethod
    def determine_times(start_time_raw: str, end_time_raw: str) -> Tuple[str, str]:
        """Determine hh:mm format of inconsistent time strings like (4:00, 5:50PM)"""
        try:
            start_hours, start_minutes = map(int, start_time_raw.split(":"))
            end_hours, end_minutes = map(
                int, end_time_raw.replace("AM", "").replace("PM", "").split(":")
            )
        except:
            return (None, None)

        # Determine meridiems
        if "PM" in end_time_raw:
            if end_hours < 12:
                end_hours += 12

            if start_hours + 12 <= end_hours:
                start_hours += 12

        return (
            f"{str(start_hours).zfill(2)}:{str(start_minutes).zfill(2)}",
            f"{str(end_hours).zfill(2)}:{str(end_minutes).zfill(2)}",
        )

    @staticmethod
    def determine_days(days_raw: str) -> List[int]:
        if days_raw:
            return list(
                map(
                    lambda day_letter: DAY_LETTERS[day_letter],
                    filter(lambda v: v != " ", days_raw),
                )
            )
        else:
            return []