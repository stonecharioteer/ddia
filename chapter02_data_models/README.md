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

1.  **Design the Schema**: Define the tables for `users`, `positions`, `education`, and `skills`. Think about the
    relationships between them (one-to-many, many-to-many).
2.  **Create a Schema File**: Write the `CREATE TABLE` statements in a `schema.sql` file.
3.  **Load the Schema**: Write a script (in Python or Go) to connect to the PostgreSQL database and execute the
    `schema.sql` file.
4.  **Generate Data**: Use a library like Mimesis (Python) to generate realistic-looking data for a complete resume.
5.  **Insert Data**: Write the application code to insert the generated data into the corresponding tables.
6.  **Query Data**: Write a query that `JOIN`s the tables to reconstruct the full resume for a user.

[Solution here](./relational_data_model.md)

### 2. Resume in MongoDB (Document Model)

**Objective**: Store the same resume from Exercise 1, but this time as a single, nested JSON document. This will
demonstrate the locality of data in a document model and how it can simplify application code.

**Tasks**:

1.  **Design the Document**: Structure the resume as a single JSON object. The `positions` and `education` will likely
    be arrays of nested objects within the main user document.
2.  **Connect and Insert**: Write a script (in Python or Go) to connect to MongoDB and insert the generated resume
    document into a collection.
3.  **Query Data**: Retrieve the entire resume with a single query.
4.  **Compare**: Reflect on the differences in the application code between the relational and document models for this
    use case.

### 3. Social Network in Neo4j (Graph Model)

**Objective**: Model a simple "followers" social graph and run queries that are very difficult or inefficient in
relational or document models.

**Tasks**:

1.  **Design the Graph**: Model users as `(:User)` nodes and the relationships between them as `[:FOLLOWS]` edges.
2.  **Connect and Create**: Write a script (in Python or Go) to connect to Neo4j.
3.  **Generate and Insert Data**: Create a few sample users and establish some `FOLLOWS` relationships between them.
4.  **Write Cypher Queries**:
    - Find all the people a specific user follows.
    - Find all the followers of a specific user.
    - **The classic graph problem**: Find all "friends of friends" for a user (i.e., the users followed by the people
      they follow), excluding the user themselves and people they already follow.
