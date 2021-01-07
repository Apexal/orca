from api.db import PostgresPoolWrapper, update_course_sections
import os
import sys
from api.parser.sis import SIS
from api.parser.registrar import Registrar

if len(sys.argv) == 1:
    print("Pass semester ids to import as command line arguments")
    exit(1)

postgres_pool = PostgresPoolWrapper(
    postgres_dsn=os.environ["POSTGRES_DSN"])
postgres_pool.init()

conn = next(postgres_pool.get_conn())
sis = SIS(os.environ["SIS_RIN"], os.environ["SIS_PIN"], )
if sis.login():
    print("Logged in to SIS")
    for semester_id in sys.argv[1:]:
        period_types = Registrar.parse_period_types(semester_id)
        print("Importing schedule for", semester_id)
        course_sections = sis.fetch_course_sections(
            semester_id, period_types=period_types)
        update_course_sections(conn, semester_id, course_sections)
else:
    print("Failed to log into SIS")
    exit(1)
