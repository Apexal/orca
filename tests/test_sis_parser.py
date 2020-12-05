import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
from api.parser.sis import SIS


def test_good_login():
    sis = SIS(os.environ["SIS_RIN"], os.environ["SIS_PIN"])
    assert sis.login()


def test_bad_login():
    sis = SIS("1234567890", "fake")
    assert not sis.login()


def test_time_parsing():
    assert SIS._to_24_hour_time("12:13 am") == "00:13"
    assert SIS._to_24_hour_time("01:00 am") == "01:00"
    assert SIS._to_24_hour_time("12:00 pm") == "12:00"
    assert SIS._to_24_hour_time("02:03 pm") == "14:03"

    assert SIS._determine_times(None) == (None, None)
    assert SIS._determine_times("10:10 am-12:00 pm") == ("10:10", "12:00")


# def test_fetch_subjects():
#     sis = SIS(os.environ['SIS_RIN'], os.environ['SIS_PIN'])
#     assert sis.login()
#     subjects = sis.fetch_subjects('202001')
#     print(subjects)
#     assert len(subjects) > 0

def test_fetch_course_sections():
    sis = SIS(os.environ['SIS_RIN'], os.environ['SIS_PIN'])
    assert sis.login()
    r = sis.fetch_course_sections('202101', subjects=['ASTR'])
    assert False