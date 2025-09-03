-- Generate a count of followers with at least 12 followers themselves for each user.

-- Use a Common Table Expression (CTE) to pre-calculate the follower count for every user.
-- This creates a temporary table called `follower_counts` that we can use later.

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
