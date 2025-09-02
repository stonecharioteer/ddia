# Chapter 2 Exercise: The Relational Model in Practice

This exercise demonstrated the core concepts of the relational model by building a practical resume database in
PostgreSQL. The primary goal was to experience the object-relational impedance mismatch firsthand—the friction that
occurs when mapping nested application objects to flat SQL tables.

## 1. Schema Design: NormalizationThe first step was to

design a normalized schema. Instead of putting all resume information into one giant table, we broke it down into
distinct entities to avoid data duplication.This resulted in five separate tables:

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

**Note**: I've written this part in Go while the data loading in Python solely to understand how to use both languages
to interact with postgres.
