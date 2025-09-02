package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	_ "github.com/lib/pq"
	"log"
	"os"
)

// -- structs to represent the Resume in Go.

type Position struct {
	Title     string         `json:"title"`
	Company   string         `json:"company"`
	StartDate string         `json:"start_date"`
	EndDate   sql.NullString `json:"end_date"`
}

type Education struct {
	University string `json:"university"`
	Degree     string `json:"name"`
	Major      string `json:"major"`
}

// This is the final, clean, nested structure we want.
type Resume struct {
	ID        int         `json:"id"`
	Name      string      `json:"name"`
	Positions []Position  `json:"positions"`
	Education []Education `json:"education"`
	Skills    []string    `json:"skills"`
}

func main() {
	// --- database connection ---
	connStr := "user=user password=password dbname=ddia sslmode=disable"
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// The ID of the user we want to fetch
	userID := 1

	// --- Query 1: Get the basic user info ---
	resume := Resume{
		Positions: []Position{},
		Education: []Education{},
		Skills:    []string{},
	}
	err = db.QueryRow("SELECT id, name FROM users WHERE id = $1", userID).Scan(&resume.ID, &resume.Name)
	if err != nil {
		if err == sql.ErrNoRows {
			fmt.Printf("No user found with ID %d\n", userID)
			os.Exit(0)
		}
		log.Fatal(err)
	}

	// --- Query 2: Get all positions for this user ---

	rows, err := db.Query("SELECT title, company, start_date, end_date FROM positions WHERE user_id = $1", userID)
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	for rows.Next() {
		var p Position
		var startDate, endDate sql.NullTime
		if err := rows.Scan(&p.Title, &p.Company, &startDate, &endDate); err != nil {
			log.Fatal(err)
		}
		if startDate.Valid {
			p.StartDate = startDate.Time.Format("2006-01-02")
		}
		if endDate.Valid {
			p.EndDate.String = endDate.Time.Format("2006-01-02")
			p.EndDate.Valid = true
		}

		resume.Positions = append(resume.Positions, p)
	}

	// --- Query 3: Get all education records for this user ---

	rows, err = db.Query("SELECT university, degree, major FROM education WHERE user_id = $1", userID)
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	for rows.Next() {
		var e Education
		if err := rows.Scan(&e.University, &e.Degree, &e.Major); err != nil {
			log.Fatal(err)
		}
		resume.Education = append(resume.Education, e)
	}

	// --- Query 4: Get all skills for this user (this is the only place we need a JOIN) ---

	rows, err = db.Query(`
		SELECT s.name
		FROM skills s
		JOIN users_skills us ON s.id = us.skill_id
		WHERE us.user_id = $1
	`, userID)
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	for rows.Next() {
		var skillName string
		if err := rows.Scan(&skillName); err != nil {
			log.Fatal(err)
		}
		resume.Skills = append(resume.Skills, skillName)
	}

	// --- Final Result: Assemble and print a JSON ---
	resumeJSON, err := json.MarshalIndent(resume, "", "  ")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(string(resumeJSON))
}
