# Chapter 2 Exercise: The Relational Model in Practice

This exercise demonstrated the core concepts of the relational model by building a practical resume database in
PostgreSQL. The primary goal was to experience the object-relational impedance mismatch firsthand—the friction that
occurs when mapping nested application objects to flat SQL tables.

## Getting Started

1. **Start PostgreSQL using Docker Compose:**

   ```bash
   docker compose up -d postgres
   ```

2. **Set up the Python environment:**

   ```bash
   uv sync
   ```

3. **Run the PostgreSQL data loader:**
   ```bash
   uv run postgres.py
   ```

## 1. Schema Design: Normalization

The first step was to design a normalized schema. Instead of putting all resume information into one giant table, we
broke it down into distinct entities to avoid data duplication.This resulted in five separate tables:

- `users`: For basic information (one user).
- `positions`: For job history (many positions per user).
- `education`: For academic history (many education entries per user).
- `skills`: A lookup table for unique skill names (many skills).
- `users_skills`: A junction table to create a many-to-many relationship between users and skills.

This design ensures that if a skill name or company name needs to be updated, it only has to be changed in one place. We
enforced data integrity using:

- `PRIMARY KEY`: To uniquely identify each row.
- `FOREIGN KEY`: To create links between tables (e.g., `positions.user_id references users.id`).
- `NOT NULL`: To ensure essential data like a user's name is always present.
- `UNIQUE`: To prevent duplicate entries in lookup tables like skills.

## 2. Data Loading: Handling Foreign Keys

The main challenge in loading the data was handling the relationships. The Python script had to:

1. Insert a row into the users table.
2. Use the RETURNING id clause to get the auto-generated user_id back from the database.
3. Use that user_id when inserting the associated rows into the positions and education tables.

For performance, we used `psycopg's cursor.copy()` method, which is the fastest way to bulk-load data into PostgreSQL.

## 3. The Impedance Mismatch: Querying the Data

This was the key takeaway. When we tried to reassemble a complete resume using a single SQL query with multiple JOINs,
the result was a "Cartesian product" with a lot of duplicated data.For a user with 3 jobs and 3 skills, the query
returned 3 x 3 = 9 rows, with the user's name and education repeated on every single line.

```sql
-- This single JOIN creates a messy, repetitive result set.
SELECT
    u.name,
    p.title,
    s.name AS skill_name
FROM users u
LEFT JOIN positions p ON u.id = p.user_id
LEFT JOIN users_skills us ON u.id = us.user_id
LEFT JOIN skills s ON us.skill_id = s.id
WHERE u.id = 1;
```

Then, running the query in `resume/postgres/query.sql` using `pgcli`:

```bash
uv run pgcli -d ddia --username user -W -h localhost
user@localhost:ddia> \i resume/postgres/query.sql
```

```txt
+---------+----------------+---------------+---------------------------+----------------+--------------+------------------------------------------------+----------+------------+
| user_id | name           | title         | company                   | position_start | position_end | university                                     | degree   | skill_name |
|---------+----------------+---------------+---------------------------+----------------+--------------+------------------------------------------------+----------+------------|
| 1       | Olimpia Haynes | Motor Racing  | Hilton Hotels Corporation | 2010-08-18     | 2020-01-06   | University of California, San Francisco (UCSF) | Bachelor | Go         |
| 1       | Olimpia Haynes | Motor Racing  | Hilton Hotels Corporation | 2010-08-18     | 2020-01-06   | University of California, San Francisco (UCSF) | Bachelor | DevOps     |
| 1       | Olimpia Haynes | Motor Racing  | Hilton Hotels Corporation | 2010-08-18     | 2020-01-06   | University of California, San Francisco (UCSF) | Bachelor | Kubernetes |
| 1       | Olimpia Haynes | Market Trader | Modern Realty             | 2010-11-01     | 2011-09-09   | University of California, San Francisco (UCSF) | Bachelor | Go         |
| 1       | Olimpia Haynes | Market Trader | Modern Realty             | 2010-11-01     | 2011-09-09   | University of California, San Francisco (UCSF) | Bachelor | DevOps     |
| 1       | Olimpia Haynes | Market Trader | Modern Realty             | 2010-11-01     | 2011-09-09   | University of California, San Francisco (UCSF) | Bachelor | Kubernetes |
| 1       | Olimpia Haynes | Resin Caster  | Happy Bear Investment     | 2020-01-21     | 2022-06-21   | University of California, San Francisco (UCSF) | Bachelor | Go         |
| 1       | Olimpia Haynes | Resin Caster  | Happy Bear Investment     | 2020-01-21     | 2022-06-21   | University of California, San Francisco (UCSF) | Bachelor | DevOps     |
| 1       | Olimpia Haynes | Resin Caster  | Happy Bear Investment     | 2020-01-21     | 2022-06-21   | University of California, San Francisco (UCSF) | Bachelor | Kubernetes |
+---------+----------------+---------------+---------------------------+----------------+--------------+------------------------------------------------+----------+------------+
```

This flat, repetitive result is difficult for an application to parse. It is fundamentally mismatched with the nested
object structure that our code wants to work with.

### The Solution: Multiple, Simple Queries

The practical solution, implemented in the Go script, was to run a series of simple, targeted queries:

1. Get the user's details.
2. Get the user's positions.
3. Get the user's education.
4. Get the user's skills.

This approach returns clean, non-duplicated lists of data that are trivial to assemble into a nested Resume struct in
Go. This pattern is much more common in real-world applications than a single, complex JOIN.

Running the Go script with `go run postgres.go`, we get:

```json
{
  "id": 1,
  "name": "Olimpia Haynes",
  "positions": [
    {
      "title": "Motor Racing",
      "company": "Hilton Hotels Corporation",
      "start_date": "2010-08-18",
      "end_date": {
        "String": "2020-01-06",
        "Valid": true
      }
    },
    {
      "title": "Market Trader",
      "company": "Modern Realty",
      "start_date": "2010-11-01",
      "end_date": {
        "String": "2011-09-09",
        "Valid": true
      }
    },
    {
      "title": "Resin Caster",
      "company": "Happy Bear Investment",
      "start_date": "2020-01-21",
      "end_date": {
        "String": "2022-06-21",
        "Valid": true
      }
    }
  ],
  "education": [
    {
      "university": "University of California, San Francisco (UCSF)",
      "name": "Bachelor",
      "major": "Information Technology"
    }
  ],
  "skills": ["Go", "DevOps", "Kubernetes"]
}
```

**Note**: I've written this part in Go while the data loading in Python solely to understand how to use both languages
to interact with postgres.

## 4. Skill Summary Query: Aggregating Data Across Tables

A common reporting need is to summarize data across the entire dataset—for example, counting how many users have each skill. This demonstrates SQL's powerful aggregation capabilities but also highlights the complexity of working with many-to-many relationships.

The summary query in `resume/postgres/summary.sql` counts how many users possess each skill:

```sql
SELECT
    s.name AS skill,
    COUNT(u.id) AS count_skills
FROM users AS u
LEFT JOIN
    users_skills AS us
    ON u.id = us.user_id
LEFT JOIN
    skills AS s
    ON us.skill_id = s.id
GROUP BY s.name ORDER BY s.name ASC;
```

This query requires:
- **Two JOINs**: One to connect users to the junction table, another to get skill names
- **GROUP BY**: To group results by skill name
- **COUNT()**: To aggregate the number of users per skill
- **LEFT JOINs**: To include skills that might have zero users (though this particular data setup won't have any)

The result shows each skill and how many users possess it, sorted alphabetically. This type of aggregation query is where SQL really shines—its declarative nature makes complex data summarization straightforward once you understand the JOIN patterns.
