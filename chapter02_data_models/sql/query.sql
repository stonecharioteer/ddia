SELECT
    u.id AS user_id,
    u.name,
    p.title,
    p.company,
    p.start_date AS position_start,
    p.end_date AS position_end,
    e.university,
    e.degree,
    s.name AS skill_name
FROM users AS u
LEFT JOIN
    positions AS p
    ON u.id = p.user_id
LEFT JOIN
    education AS e
    ON u.id = e.user_id
LEFT JOIN
    users_skills AS us
    ON u.id = us.user_id
LEFT JOIN
    skills AS s
    ON us.skill_id = s.id
WHERE
    u.id = 1;
