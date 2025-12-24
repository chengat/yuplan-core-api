package models

import "time"

type Section struct {
	ID            string    `json:"id"`
	SectionID     string    `json:"section_id"`
	Letter		  string    `json:"letter"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}