from api.db import PostgresPoolWrapper, update_course_sections
import os
import sys
from api.parser.sis import SIS
from api.parser.registrar import Registrar

semester_id = sys.argv[1]

postgres_pool = PostgresPoolWrapper(postgres_dsn=os.environ["POSTGRES_DSN"])
postgres_pool.init()

conn = next(postgres_pool.get_conn())
period_types = Registrar.parse_period_types(semester_id)
sis = SIS(os.environ["SIS_RIN"], os.environ["SIS_PIN"], period_types)
if sis.login():
    print("Logged in to SIS")
    course_sections = sis.fetch_course_sections(semester_id)
    update_course_sections(conn, semester_id, course_sections)
else:
    exit(1)
