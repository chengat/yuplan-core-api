package models

import "time"

type Instructor struct {
	ID            string     `json:"id"`
	FirstName     string     `json:"first_name"`
	LastName      string     `json:"last_name"`
	RateMyProfLink *string   `json:"rate_my_prof_link,omitempty"`
	SectionID     *string    `json:"section_id,omitempty"`
	CreatedAt     time.Time  `json:"created_at"`
	UpdatedAt     time.Time  `json:"updated_at"`
}

