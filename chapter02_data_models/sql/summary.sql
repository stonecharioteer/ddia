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
