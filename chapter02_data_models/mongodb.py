"""MongoDB schema creator"""
import random
import pprint
from pymongo import MongoClient
from bson.code import Code
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


def summary():
    """Summarizes the skills against the number of users that have them."""
    with MongoClient("mongodb://localhost:27017") as client:
        db = client["ddia"]
        resumes_collection = db["resumes"]
        # This is the aggregation pipeline, defined as a list of stages.
        pipeline = [
            {
                # stage 1: Deconstruct the `skills` array
                # this craetes a separate document for each skill a user has.
                "$unwind": "$skills"
            },
            {
                # stage 2: Group the documents by the skill name
                # the `_id` field in the group stage specifies the key to group by.
                "$group": {
                    "_id": "$skills",

                    "count": { # For each document in a group, add one to the count.
                        "$sum": 1
                    }
                }
            },
            {
                # Stage 3 (Optional): Sort the results by the skill name
                "$sort": {"_id": 1}
            }
        ]
        print("Executing the aggregation pipeline")
        pprint.pprint(pipeline)
        print("-"*30)
        results = resumes_collection.aggregate(pipeline)
        print("Skill counts:")
        for doc in results:
            pprint.pprint(doc)

def summary_mapreduce():
    """
    Connects to MongoDB and runs a MapReduce job to count skills.
    Note: This is a legacy feature, replaced by the Aggregation Pipeline.
    """
    with MongoClient("mongodb://localhost:27017") as client:
        db = client["ddia"]
        resumes_collection = db["resumes"]

        # --- 1. Define the Map Function (in JavaScript) ---
        # This function is executed for every single document in the collection.
        # Its job is to "emit" one or more key-value pairs.
        mapper = Code("""
            function() {
                // 'this' refers to the document being processed.
                if (this.skills) {
                    // Loop through the skills array in the document.
                    for (var i = 0; i < this.skills.length; i++) {
                        // For each skill, emit a key-value pair.
                        // The key is the skill name (e.g., "Python").
                        // The value is 1, representing a single count.
                        emit(this.skills[i], 1);
                    }
                }
            }
        """)

        # --- 2. Define the Reduce Function (in JavaScript) ---
        # This function is called for each unique key emitted by the map phase.
        # It receives the key (e.g., "Python") and an array of all the values
        # emitted for that key (e.g., [1, 1, 1, 1, ...]).
        reducer = Code("""
            function(key, values) {
                // Sum up all the 1s to get the total count for this skill.
                return Array.sum(values);
            }
        """)

        print("Executing MapReduce job...")
        print("-" * 30)

        # --- 3. Execute the MapReduce Job ---
        # Note: MapReduce was deprecated in MongoDB 4.4 and removed in PyMongo 4.x
        # Using the database command directly to demonstrate the legacy approach
        try:
            result = db.command("mapReduce", "resumes", 
                              map=mapper, 
                              reduce=reducer, 
                              out="skill_counts")
            
            print("MapReduce job completed successfully")
            print("Skill Counts (from MapReduce output collection):")
            # Query the output collection to see the final results
            skill_counts_collection = db["skill_counts"]
            for doc in skill_counts_collection.find().sort("_id"):
                # The result format is {'_id': skill_name, 'value': count}
                pprint.pprint(doc)
                
        except Exception as e:
            print(f"MapReduce failed (likely deprecated): {e}")
            print("This demonstrates why MapReduce was replaced by aggregation pipelines!")

if __name__ == "__main__":
    total = 50
    print(f"Inserting {total} resumes")
    for i in range(total):
        load_one_resume()
    print("Showing how to filter resumes.")
    filter_resumes()
    print("Generating summary of skill counts.")
    summary()
    print("Generating the summary using mapreduce")
    summary_mapreduce()
    print("Done")

