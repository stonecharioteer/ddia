# Graph Data Model Exercise - PostgreSQL Groundwork

## Overview

Before diving into Neo4j for the graph model exercise, we've established a baseline using PostgreSQL to demonstrate the complexity of graph-like queries in a relational database. This groundwork showcases the "pain point" that graph databases are designed to solve.

## PostgreSQL Schema Updates

### New Table: `followers`

Added a junction table to represent user-follower relationships:

```sql
CREATE TABLE followers (
    user_id integer REFERENCES users (id),
    follower_id integer REFERENCES users (id),
    PRIMARY KEY (user_id, follower_id)
)
```

This table models the social graph where:
- `user_id`: The person being followed
- `follower_id`: The person doing the following

### Data Population

The `postgres.py` script now includes:

1. **`add_followers()` function**: Generates realistic follower relationships
   - Each user follows 5-20 other users randomly
   - Ensures no self-following
   - Creates diverse connection patterns for interesting queries

## Complex Relationship Queries

### 1. Friends of Friends Query (`followers.sql`)

Implements the classic "friends of friends" problem that demonstrates SQL's limitations with graph traversal:

```sql
-- Find people followed by those you follow (excluding yourself and direct follows)
SELECT DISTINCT fof_user.id, fof_user.name
FROM followers AS f1
JOIN followers as f2 on f1.user_id = f2.follower_id
JOIN users AS fof_user ON f2.user_id = fof_user.id
WHERE f1.follower_id = 1
  AND f2.user_id != 1
  AND f2.user_id NOT IN (
    SELECT user_id FROM followers WHERE follower_id = 1
  );
```

This query showcases:
- Complex self-joins on the `followers` table
- Multiple filtering conditions to exclude unwanted results
- The awkwardness of expressing path-finding logic in SQL

### 2. Influential Followers Analysis (`follower_with_ge_x_followers.sql`)

Demonstrates hierarchical analysis using CTEs to find users with highly-connected followers:

```sql
WITH follower_counts AS (
    SELECT user_id, COUNT(follower_id) AS num_followers
    FROM followers GROUP BY user_id
)
SELECT u.name, COUNT(f1.follower_id) as influential_follower_count
FROM users u
LEFT JOIN followers f1 ON u.id = f1.user_id
JOIN follower_counts fc ON f1.follower_id = fc.user_id
WHERE fc.num_followers >= 12
GROUP BY u.name
HAVING COUNT(f1.follower_id) > 12
ORDER BY influential_follower_count DESC;
```

This query illustrates:
- Multi-step aggregation using Common Table Expressions
- Complex joining patterns for relationship analysis
- The verbosity required for what should be intuitive graph operations

## The Pain Points

These PostgreSQL implementations highlight why graph databases exist:

1. **Complex Joins**: Multiple self-joins make queries hard to read and reason about
2. **Performance**: Each relationship traversal requires expensive joins
3. **Scalability**: Deep relationship queries become exponentially complex
4. **Cognitive Load**: SQL doesn't map naturally to graph thinking

## Next Steps

With this relational baseline established, the Neo4j implementation will demonstrate how graph databases solve these problems with:
- Natural path-finding syntax in Cypher
- Efficient graph traversal algorithms
- Intuitive relationship modeling
- Better performance for complex relationship queries

The contrast between these SQL queries and their Cypher equivalents will illustrate the fundamental advantages of choosing the right data model for graph problems.