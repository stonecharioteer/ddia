# Graph vs. Relational Models for Social Graphs

When modeling highly connected data like a social network, both relational (SQL) and graph (Cypher) databases can be used, but they offer different approaches and trade-offs. This section compares the two models for the same problem of analyzing a social graph.

## The Relational (SQL) Approach

In a relational database, we would typically model a social network with at least two tables:

*   `users`: Stores information about each user (e.g., `id`, `name`).
*   `followers`: A join table that represents the relationship between users, with columns like `user_id` and `follower_id`.

To query for relationships, we need to perform `JOIN` operations between these tables. For more complex queries, such as finding "friends of friends" or "influential followers," the SQL queries can become quite complex, often requiring multiple self-joins, subqueries, or Common Table Expressions (CTEs).

### SQL Query Examples

#### Influential Followers

This query finds users who have a certain number of "influential" followers (followers who themselves have a minimum number of followers).

```sql
-- Use a Common Table Expression (CTE) to pre-calculate the follower count for every user.
WITH follower_counts as (
    SELECT
        user_id,
        COUNT(follower_id) AS num_followers
    FROM
        followers
    GROUP BY
        user_id
)
-- now we write the main query that uses our temporary table
SELECT
    u.name,
    -- we count the followers from the main `followers` table (aliased as f1)
    COUNT(f1.follower_id) as influential_follower_count
FROM
    users u
-- Join to find the direct followers of each user
LEFT JOIN
  followers f1 ON u.id = f1.user_id
-- Join again to our temporary table to check the follower count of each follower.
JOIN
  follower_counts fc ON f1.follower_id = fc.user_id
WHERE
  -- this is the filter: only include followers who have at least X followers themselves
  fc.num_followers >= 12
GROUP By
  u.name
HAVING
    COUNT(f1.follower_id) > 12 -- filter the groups after counting
ORDER BY
  influential_follower_count DESC;
```

#### Friends of Friends

This query finds "friends of friends" for a given user.

```sql
SELECT DISTINCT
  fof_user.id,
  fof_user.name
FROM
  followers AS f1
-- This is the self-join. We're linking the person followed in the first hop
-- to the person doing the following in the second hop
JOIN
  followers as f2 on f1.user_id = f2.follower_id
-- we also need to join to the users table to get the final user's name
JOIN
  users AS fof_user ON f2.user_id = fof_user.id
WHERE
  -- 1. Start with our user, the follower in the first hop
  f1.follower_id = 1
  -- 2. Exclude the original user from the final result
  and f2.user_id != 1

  -- 3. Exclude anyone that our user already follows directly
  AND f2.user_id NOT in (
    SELECT user_id FROM followers WHERE follower_id = 1
);
```

## The Graph (Cypher) Approach

In a graph database like Neo4j, the data model is more intuitive for social networks. Users are represented as `User` nodes, and the "follows" relationship is a directed edge between them. This makes the queries for relationship-based questions much more straightforward.

### Cypher Query Examples

#### Influential Followers

```cypher
MATCH (follower:User)-[:FOLLOWS]->(u:User)
WHERE size((follower)<-[:FOLLOWS]-()) >= $minFollowers
WITH u, count(follower) AS influentialFollowerCount
WHERE influentialFollowerCount >= $minFollowers
RETURN u.name AS userName, influentialFollowerCount
ORDER BY influentialFollowerCount DESC
```

#### Friends of Friends

```cypher
MATCH (u:User {uuid: $uuid})-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(fof:User)
WHERE u <> fof AND NOT (u)-[:FOLLOWS]->(fof)
RETURN DISTINCT fof.name AS friendOfFriendName
```

## Comparison and Caveats

| Feature                 | SQL (Relational)                                                                                             | Cypher (Graph)                                                                                                     |
| ----------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **Query Readability**   | Can be complex and hard to read, especially with multiple joins and subqueries. The logic is less intuitive. | The syntax is designed to mirror the graph pattern, making queries more readable and easier to write.              |
| **Performance**         | Deep joins (like for "friends of friends") can be slow and resource-intensive as the number of relationships grows. | Graph databases are optimized for traversing relationships, so these types of queries are typically much faster. |
| **Data Modeling**       | The schema is rigid. Adding new types of relationships or entities can require schema migrations.              | The schema is flexible. It's easy to add new node labels, properties, and relationship types without migrations. |
| **Caveats**             | Best for well-structured data with few relationships. Can be faster for simple aggregations over the whole dataset. | Can be less efficient for large-scale aggregations that are not based on relationships.                          |

For a problem like analyzing a social graph, a graph database is generally the better call. The data model is more natural, and the queries are more intuitive and performant for the types of questions you would typically ask.

# Graph Data Models with Neo4j

This document summarizes the exercises performed with Neo4j to understand graph data models, as described in Chapter 2 of "Designing Data-Intensive Applications" by Martin Kleppmann. The exercises involve creating a social graph, populating it with users and relationships, and querying it to find interesting patterns.

## Data Model

The social graph is modeled using the following components:

*   **Nodes**:
    *   `:User`: Represents a user in the social network. Each user has the following properties:
        *   `name`: The user's full name (e.g., "Alice").
        *   `uuid`: A unique identifier for the user. A uniqueness constraint is enforced on this property to ensure data integrity.

*   **Relationships**:
    *   `:FOLLOWS`: Represents a directed relationship from one user to another (e.g., `(User1)-[:FOLLOWS]->(User2)`).

## Data Population

The graph is populated using a Python script (`neo4j_social.py`) that connects to a Neo4j database. The script performs the following actions:

1.  **Connects to Neo4j**: Establishes a connection to the database using the official Python driver.
2.  **Ensures Uniqueness**: Creates a uniqueness constraint on the `uuid` property of `:User` nodes to prevent duplicate users.
3.  **Bulk Creation**: Uses the `UNWIND` clause for efficient bulk creation of users and their `:FOLLOWS` relationships. This is a more performant approach than creating nodes and relationships one by one.

## Queries

The following Cypher queries are used to retrieve information from the graph:

1.  **Finding Followers**: A simple query to find all the users who follow a given user.
    ```cypher
    MATCH (follower:User)-[:FOLLOWS]->(user:User {uuid: $uuid})
    RETURN follower.name
    ```

2.  **Finding Influential Followers**: A more complex query to find users who have a certain number of "influential" followers. An influential follower is defined as a user who has a minimum number of followers themselves.
    ```cypher
    MATCH (follower:User)-[:FOLLOWS]->(u:User)
    WHERE size((follower)<-[:FOLLOWS]-()) >= $minFollowers
    WITH u, count(follower) AS influentialFollowerCount
    WHERE influentialFollowerCount >= $minFollowers
    RETURN u.name AS userName, influentialFollowerCount
    ORDER BY influentialFollowerCount DESC
    ```

3.  **Friends of Friends**: A query to find users who are "friends of friends" (i.e., followed by the people you follow), but whom you don't follow directly.
    ```cypher
    MATCH (u:User {uuid: $uuid})-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(fof:User)
    WHERE u <> fof AND NOT (u)-[:FOLLOWS]->(fof)
    RETURN DISTINCT fof.name AS friendOfFriendName
    ```

These exercises demonstrate the flexibility and power of graph data models for representing and querying highly connected data, such as social networks.
