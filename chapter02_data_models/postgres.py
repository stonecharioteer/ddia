import os
import random
import pprint
import pathlib
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


CONN_STRING = "host='{}' dbname='{}' user='{}' password='{}'".format(
    "localhost", "ddia", "user", "password"
)


def populate_initial_skills():
    """Loads a list of skills."""
    skills_list = [
        "Python",
        "Go",
        "Docker",
        "PostgreSQL",
        "Kubernetes",
        "React",
        "VueJS",
        "AWS",
        "GCP",
        "Azure",
        "Terraform",
        "CI/CD",
        "DevOps",
        "NextJS",
        "GenAI",
        "LangChain/LangGraph",
        "AI Agents",
    ]
    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cursor:
            skills_to_add_tuples = [(skill,) for skill in skills_list]
            cursor.executemany(
                "INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;",
                skills_to_add_tuples,
            )
        print("Initial skills populated/verified.")


def load_data(num_users=5000):
    """Loads generated data into the database tables"""
    from mimesis import Person, Finance, Datetime
    from mimesis.locales import Locale

    print(f"Generating data for {num_users} users.")

    person = Person(Locale.EN)
    business = Finance(Locale.EN)
    datetime = Datetime(Locale.EN)

    users_data = [(person.full_name(),) for _ in range(num_users)]

    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM skills;")
            skill_map = {row[1]: row[0] for row in cursor.fetchall()}

            # COPY is the fastest way to insert, but it doesn't support RETURNING.
            # So we insert users first and then fetch their IDs.
            with cursor.copy("COPY users (name) from STDIN") as copy:
                for user_row in users_data:
                    copy.write_row(user_row)

            # Fetch the IDs of the users we just inserted.
            # This assumes IDs are sequential.
            cursor.execute(f"SELECT id from users ORDER BY id DESC LIMIT {num_users};")
            user_ids = [row[0] for row in reversed(cursor.fetchall())]
            print("Inserted {} users.".format(len(user_ids)))

            positions_data = []
            education_data = []
            users_skills_data = []

            skill_names = list(skill_map.keys())
            for user_id in user_ids:
                # generate positions for this user
                for _ in range(random.randint(1, 3)):
                    start = datetime.date(start=2010, end=2020)
                    end = datetime.date(start=start.year + 1, end=2024)
                    positions_data.append(
                        (user_id, person.occupation(), business.company(), start, end)
                    )

                # generate education for this user
                start = datetime.date(start=2006, end=2010)
                end = datetime.date(start=start.year + 1, end=2024)
                major = random.choice(
                    [
                        "Computer Science",
                        "Machine Learning",
                        "Artificial Intelligence",
                        "Information Technology",
                        "Robotics",
                        "Data Science",
                        "Mathematics",
                        "Statistics",
                        "Statistical Learning",
                    ]
                )
                education_data.append(
                    (
                        user_id,
                        person.university(),
                        person.academic_degree(),
                        major,
                        start,
                        end,
                    )
                )
                user_skills = random.sample(skill_names, random.randint(1, 10))
                for skill_name in user_skills:
                    users_skills_data.append((user_id, skill_map[skill_name]))
            print("Data generation complete. Starting batch inserts...")
            with cursor.copy(
                "COPY positions (user_id, title, company, start_date, end_date) FROM STDIN"
            ) as copy:
                for pos_row in positions_data:
                    copy.write_row(pos_row)
            print("Inserted {} positions.".format(len(positions_data)))

            with cursor.copy(
                "COPY education (user_id, university, degree, major, start_date, end_date) FROM STDIN"
            ) as copy:
                for edu_row in education_data:
                    copy.write_row(edu_row)
            print("Inserted {} education records.".format(len(education_data)))

            with cursor.copy("COPY users_skills (user_id, skill_id) FROM STDIN") as copy:
                for us_row in users_skills_data:
                    copy.write_row(us_row)
            print("Inserted {} skills to users.".format(len(users_skills_data)))


def create_schemas():
    """Creates schemas in the database using `schemas.sql` file"""
    with psycopg.connect(CONN_STRING, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            schema_file_path = (
                pathlib.Path(os.path.realpath(__file__)).parent
                / "resume/postgres/schema.sql"
            )
            assert schema_file_path.exists(), "Schema file doesn't exist at {}".format(
                schema_file_path
            )
            with open(schema_file_path, "r") as f:
                schema = f.read()
            cursor.execute(schema)
            conn.commit()
            print("Tables created successfully.")
            cursor.execute(
                "select tablename from pg_catalog.pg_tables WHERE schemaname = 'public';"
            )
            public_tables = sorted([row["tablename"] for row in cursor.fetchall()])
            pprint.pprint("Tables created in `public` schema: {}".format(public_tables))


def add_followers():
    """Add followers"""
    print("Creating follower relationships")
    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM USERS;")
            user_ids = [row[0] for row in cursor.fetchall()]
            if len(user_ids) < 2:
                raise Exception("Not enough users to create follower relationships")

            follower_data = []
            for follower_id in user_ids:
                num_to_follow = random.randint(5, 20)
                potential_users = [uid for uid in user_ids if uid != follower_id]
                num_to_follow = min(num_to_follow, len(potential_users))
                users_to_follow = random.sample(potential_users, num_to_follow)
                for user_id in users_to_follow:
                    follower_data.append((user_id, follower_id))
            with cursor.copy("COPY followers (user_id, follower_id) FROM STDIN") as copy:
                for row in follower_data:
                    copy.write_row(row)
            print(f"Inserted {len(follower_data)} follower relationships")


def main():
    print("Creating schemas in postgres")
    create_schemas()
    print("Populating skills.")
    populate_initial_skills()
    load_data(num_users=5000)
    add_followers()
    print("Done!")


if __name__ == "__main__":
    load_dotenv()
    main()
