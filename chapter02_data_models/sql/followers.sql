-- The Goal: Find "Friends of Friends" in SQL
-- We want to find all the unique users who are followed by the people that a specific user (let's say user_id = 1) follows.
-- In plain English, the logic is:
-- Find all the people User 1 follows (let's call them "friends").
-- Then, find all the people that those "friends" follow.
-- From that final list, make sure to exclude User 1 themselves and anyone User 1 already follows directly.
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

