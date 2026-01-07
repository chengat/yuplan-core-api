package models

import "time"

type Course struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Code        string    `json:"code"`
	Credits     float64   `json:"credits"`
	Description *string   `json:"description"`
	Faculty     string    `json:"faculty_id"`
	Term		string    `json:"term"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}
