import os
import random
import pprint
import pathlib
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


CONN_STRING = "host='{}' dbname='{}' user='{}' password='{}'".format(
    "localhost", "ddia", "user", "password"
)


def load_data():
    """Loads generated data into the database tables"""
    from mimesis import Person, Finance, Datetime
    from mimesis.locales import Locale

    person = Person(Locale.EN)
    business = Finance(Locale.EN)
    datetime = Datetime(Locale.EN)
    with psycopg2.connect(CONN_STRING) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            user_name = person.full_name()
            cursor.execute(
                "INSERT INTO users (name) VALUES (%s) RETURNING id;", (user_name,)
            )
            user_id = cursor.fetchone()["id"]
            print(f"Inserted user '{user_name}` with ID: {user_id}")
            for _ in range(2):
                start = datetime.date(start=2010, end=2023)
                end = datetime.date(start=start.year + 1, end=2024)
                cursor.execute(
                    "INSERT INTO positions (user_id, title, company, start_date, end_date) VALUES (%s, %s, %s, %s, %s);",
                    (user_id, person.occupation(), business.company(), start, end),
                )
            print(f"Inserted positions for user_id: {user_id}")
            for _ in range(1):
                start = datetime.date(start=2006, end=2010)
                end = datetime.date(start=start.year + 4, end=2014)
                major = random.choice(
                    [
                        "Computer Science",
                        "Artificial Intelligence",
                        "Data Science",
                        "Statistics",
                        "Computational Mathematics",
                        "Machine Learning",
                    ]
                )

                cursor.execute(
                    "INSERT INTO education (user_id, university, degree, major, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        user_id,
                        person.university(),
                        person.academic_degree(),
                        major,
                        start,
                        end,
                    ),
                )
            print(f"Inserted education for user_id: {user_id}")

            skills_to_add = ["Python", "Go", "Docker", "PostgreSQL", "Kubernetes"]
            skill_ids = {}
            for skill_name in skills_to_add:
                cursor.execute(
                    "INSERT INTO skills (name) VALUES (%s) ON CONFLICT DO NOTHING;",
                    (skill_name,),
                )

            cursor.execute(
                "SELECT id, name FROM skills WHERE name = ANY(%s)", (skills_to_add,)
            )
            for row in cursor.fetchall():
                skill_ids[row["name"]] = row["id"]

            print(f"Inserted Skills: {list(skill_ids.keys())}")

            for skill_id in skill_ids.values():
                cursor.execute(
                    "INSERT INTO users_skills (user_id, skill_id) VALUES (%s, %s)",
                    (user_id, skill_id),
                )
            print(f"Linked skills for user_id: {user_id}")


def create_schemas():
    """Creates schemas in the database using `schemas.sql` file"""
    with psycopg2.connect(CONN_STRING) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            schema_file_path = (
                pathlib.Path(os.path.realpath(__file__)).parent
                / "resume/postgres/schema.sql"
            )
            assert schema_file_path.exists(), "Schema file doesn't exist"
            with open(schema_file_path, "r") as f:
                schema = f.read()
            cursor.execute(schema)
            conn.commit()
            print("Created tables")
            cursor.execute("select * from pg_catalog.pg_tables")
            result = cursor.fetchall()
            public_tables = [row[1] for row in result if row[0] == "public"]
            public_tables.sort()
            pprint.pprint("Tables created: {}".format(public_tables))


def main():
    print("Creating schemas in postgres")
    create_schemas()
    for _ in range(5000):
        load_data()


if __name__ == "__main__":
    load_dotenv()
    main()
