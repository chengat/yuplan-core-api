package models

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestInstructorModel(t *testing.T) {
	rmpLink := "https://www.ratemyprofessors.com/search/professors/?q=John+Doe"
	sectionID := "section-1"
	
	instructor := Instructor{
		ID:            "instructor-1",
		FirstName:     "John",
		LastName:      "Doe",
		RateMyProfLink: &rmpLink,
		SectionID:     &sectionID,
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}

	assert.Equal(t, "instructor-1", instructor.ID)
	assert.Equal(t, "John", instructor.FirstName)
	assert.Equal(t, "Doe", instructor.LastName)
	assert.NotNil(t, instructor.RateMyProfLink)
	assert.Equal(t, rmpLink, *instructor.RateMyProfLink)
	assert.NotNil(t, instructor.SectionID)
	assert.Equal(t, sectionID, *instructor.SectionID)
}

func TestInstructorModel_WithNilFields(t *testing.T) {
	instructor := Instructor{
		ID:        "instructor-2",
		FirstName: "Jane",
		LastName:  "Smith",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	assert.Equal(t, "instructor-2", instructor.ID)
	assert.Equal(t, "Jane", instructor.FirstName)
	assert.Equal(t, "Smith", instructor.LastName)
	assert.Nil(t, instructor.RateMyProfLink)
	assert.Nil(t, instructor.SectionID)
}

