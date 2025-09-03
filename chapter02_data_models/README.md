# DDIA Chapter 2: Data Models and Query Languages - Practical Exercises

This project contains a series of hands-on exercises to explore the concepts from Chapter 2 of Martin Kleppmann's
"Designing Data-Intensive Applications". We will use different data models (relational, document, and graph) to
represent similar data, and use both Python and Go to interact with the databases.

## Technology Stack

- **Databases**: PostgreSQL, MongoDB, Neo4j (running in Docker)
- **Languages**: Python, Go
- **Tooling**: Docker Compose, uv, mise

## Exercises

### 1. Resume in PostgreSQL (Relational Model)

**Objective**: Model a resume using a normalized relational schema. This exercise highlights how to structure connected
data in a relational database and the need for JOINs to reassemble it.

**Tasks**:

1. **Design the Schema**: Define the tables for `users`, `positions`, `education`, and `skills`. Think about the
   relationships between them (one-to-many, many-to-many).
2. **Create a Schema File**: Write the `CREATE TABLE` statements in a `schema.sql` file.
3. **Load the Schema**: Write a script (in Python or Go) to connect to the PostgreSQL database and execute the
   `schema.sql` file.
4. **Generate Data**: Use a library like Mimesis (Python) to generate realistic-looking data for a complete resume.
5. **Insert Data**: Write the application code to insert the generated data into the corresponding tables.
6. **Query Data**: Write a query that `JOIN`s the tables to reconstruct the full resume for a user.

[Solution here](./relational_data_model.md)

### 2. Resume in MongoDB (Document Model)

**Objective**: Store the same resume from Exercise 1, but this time as a single, nested JSON document. This will
demonstrate the locality of data in a document model and how it can simplify application code.

**Tasks**:

1. **Design the Document**: Structure the resume as a single JSON object. The `positions` and `education` will likely be
   arrays of nested objects within the main user document.
2. **Connect and Insert**: Write a script (in Python or Go) to connect to MongoDB and insert the generated resume
   document into a collection.
3. **Query Data**: Retrieve the entire resume with a single query.
4. **Compare**: Reflect on the differences in the application code between the relational and document models for this
   use case.

[Solution here](./document_data_model.md)

### 3: The Graph Model vs. The Relational Model

**Objective**: To understand the strengths of the graph data model by directly comparing how a relational database and a
graph database handle a complex relationship query. This exercise will demonstrate why graph databases excel at
"many-to-many" and path-finding problems, as discussed in Chapter 2.

**The Challenge**: Find "friends of friends" for a user—that is, the users followed by the people they follow.

[Solution here](./graph_data_model.md)

#### Task 1: The Relational Approach (The Pain Point)

Before touching Neo4j, we first need to establish a baseline by solving this problem with the tools we already have.

1.  **Create the Relationship**: In your PostgreSQL database, add a new junction table called `followers` with two
    columns: `user_id` and `follower_id`.
2.  **Populate Data**: Write a simple Python script to populate this table with some sample data. Make sure some users
    have followers in common to make the query interesting.
3.  **Write the SQL Query**: Write a **single SQL query** that, for a given `user_id`, finds all of their "friends of
    friends."
    - **Hint**: This is a notoriously difficult query in SQL. It will likely require multiple `JOIN`s on the same table
      (a "self-join") and careful filtering with `WHERE` clauses to exclude the original user and people they already
      follow.
    - **Goal**: Feel the complexity and awkwardness of expressing this path-finding logic in SQL.

---

#### Task 2: The Graph Approach (The Solution)

Now, let's solve the exact same problem in a database that is designed for it.

1.  **Design the Graph**: Model users as nodes with the label `(:User {name: '...'})` and the relationships between them
    as directed edges with the label `[:FOLLOWS]`.
2.  **Connect and Create**: Write a script (in Python or Go) to connect to your Neo4j instance. You'll need the `neo4j`
    Python driver: `pip install neo4j`.
3.  **Generate and Insert Data**: In your script, create a few sample `User` nodes and establish some `:FOLLOWS`
    relationships between them to match the data you created in PostgreSQL.
4.  **Write Cypher Queries**: Write simple, readable queries in Cypher to answer the following questions:
    - Find all the people a specific user follows.
    - Find all the followers of a specific user.
    - **The "Friends of Friends" Query**: Find all "friends of friends" for a user, excluding the user themselves and
      people they already follow.

---

#### Task 3: Compare and Reflect

Once you have both solutions working, compare the SQL query from Task 1 with the Cypher query from Task 2. Reflect on
the following questions:

- How much longer and more complex was the SQL query?
- How well did the Cypher query `MATCH (u:User)-[:FOLLOWS]->(friend)-[:FOLLOWS]->(fof) ...` map to the English-language
  description of the problem?
- Based on this experience, for what kinds of applications or features would a graph database be a more natural fit than
  a relational one?


## Getting Started

1. **Prerequisites**: Docker, Python 3.13+, Go (via mise)
2. **Start Services**: `docker compose up -d`
3. **Install Dependencies**: `uv sync`
4. **Run Scripts**: Follow the instructions in each exercise section.

## CLI Tool (`script.py`)

This chapter includes a command-line interface (CLI) tool to orchestrate the database operations for all three data models. You can run it using `uv run python script.py --help`.

### PostgreSQL Commands

Use `uv run python script.py postgres --help` to see the full list of commands.

- `create-schemas`: Creates the necessary tables in PostgreSQL.
- `populate-data`: Populates the database with a specified number of users and their skills.
- `count-skills`: Counts the number of users who have each skill.
- `suggest-follows`: Suggests users to follow based on a "friends of friends" analysis.
- `list-influential-followers`: Lists users who have influential followers.

### MongoDB Commands

Use `uv run python script.py mongo --help` to see the full list of commands.

- `populate-data`: Generates and inserts a specified number of fake resumes into MongoDB.
- `query-resumes`: Demonstrates various queries on the resume data.
- `count-skills`: Counts skills using the aggregation pipeline.
- `count-skills-mapreduce`: Counts skills using the legacy MapReduce framework.
- `purge-data`: Clears all data from the MongoDB collections.

### Neo4j Commands

Use `uv run python script.py neo4j --help` to see the full list of commands.

- `create-user`: Creates a single user node.
- `create-social-graph`: Creates a social graph with a specified number of users.
- `get-followers-of-random-user`: Queries for the followers of a random user.
- `get-influential-followers`: Queries for influential followers.
- `get-friends-of-friends`: Queries for "friends of friends".

## What You'll Learn

- The "object-relational impedance mismatch" in practice
- How data locality in document models can simplify application code
- The trade-offs between schema-on-write (relational) and schema-on-read (document)
- How to choose the right data model for the job

