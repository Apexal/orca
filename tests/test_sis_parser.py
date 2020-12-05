import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from api.parser.sis import SIS

def test_good_login():
    sis = SIS(os.environ['SIS_RIN'], os.environ['SIS_PIN'])
    assert sis.login()

def test_bad_login():
    sis = SIS('1234567890', 'fake')
    assert not sis.login()

def test_fetch_semester_subjects():
    sis = SIS(os.environ['SIS_RIN'], os.environ['SIS_PIN'])
    assert sis.login()
    subjects = sis.fetch_semester_subjects('202001')
    print(subjects)
    assert len(subjects) > 0

def test_fetch_course_sections_page():
    sis = SIS(os.environ['SIS_RIN'], os.environ['SIS_PIN'])
    assert sis.login()
    r = sis.fetch_course_sections('202001')
    assert False