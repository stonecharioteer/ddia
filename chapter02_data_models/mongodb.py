"""MongoDB schema creator"""
import random
import pprint
from pymongo import MongoClient
from mimesis import Person, Finance, Datetime
from mimesis.locales import Locale


def get_major():
    return random.choice([
        "Artificial Intelligence",
        "Computer Science",
        "Data Science",
        "Information Technology",
        "Machine Learning",
        "Mathematics",
        "Robotics",
        "Statistical Learning",
        "Statistics",
    ])

def get_random_skills():
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
    return random.sample(skills_list, random.randint(3, 7))

def load_one_resume():
    """Generates one fake resume and inserts it into MongoDB"""
    person = Person(Locale.EN)
    business = Finance(Locale.EN)
    datetime = Datetime(Locale.EN)

    resume_doc = {
        "name": person.full_name(),
        "positions": [],
        "education": [],
        "skills": []
    }

    for _ in range(random.randint(1, 3)):
        start = datetime.date(start=2010, end=2020)
        end = datetime.date(start=start.year+1, end=2024)

        resume_doc["positions"].append({
            "title": person.occupation(),
            "company": business.company(),
            "start_date": start.isoformat(),
            "end_date": end.isoformat()
        })

    start = datetime.date(start=2006, end=2010)
    end = datetime.date(start=start.year + 1, end=2014)
    resume_doc["education"].append({
        "university": person.university(),
        "degree": person.academic_degree(),
        "major": get_major(),
        "start_date": start.isoformat(),
        "end_date": end.isoformat()
    })

    resume_doc["skills"] = get_random_skills()

    client = MongoClient("mongodb://localhost:27017")
    db = client["ddia"]
    resumes_collection = db["resumes"]
    _insert_result = resumes_collection.insert_one(resume_doc)
    # print("Successfully inserted document with ID: {}".format(_insert_result.inserted_id))
    # retrieved_doc = resumes_collection.find_one({"_id": insert_result.inserted_id})
    # pprint.pprint(retrieved_doc)
    client.close()


def filter_resumes():

    # --- 1. Define all queries and their descriptions in a data structure ---
    # This makes the code data-driven and easy to extend.
    QUERIES = [
        {
            "description": "Resumes with 'Python' as a skill",
            "query": {"skills": "Python"},
        },
        {
            "description": "Resumes with skills containing Python AND AWS",
            "query": {"skills": {"$all": ["Python", "AWS"]}},
        },
        {
            "description": "Resumes with skills containing Python OR AWS, AND a major in Statistics",
            "query": {
                "skills": {"$in": ["Python", "AWS"]},
                "education.major": "Statistics",
            },
        },
        {
            "description": "Resumes with skills containing Python OR AWS, AND a PhD in Statistics",
            "query": {
                "skills": {"$in": ["Python", "AWS"]},
                "education": {
                    "$elemMatch": {"degree": "PhD", "major": "Statistics"}
                },
            },
        },
    ]
    with MongoClient("mongodb://localhost:27017") as client:
        db = client["ddia"]
        resumes_collection = db["resumes"]
        for i, q in enumerate(QUERIES):
            description = q["description"]
            query = q["query"]
            print(f"\n--- Query {i+1}: {description} ---")
            count = resumes_collection.count_documents(query)
            print(f"Found {count} resumes for query: ")
            pprint.pprint(query)


if __name__ == "__main__":
    total = 5000
    for i in range(total):
        load_one_resume()
        print(f"Inserted {i+1}/{total}")
    filter_resumes()
    print("Done")

