package models

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestLabModel(t *testing.T) {
	times := `[{"day": "M", "time": "10:30", "duration": "110"}]`
	lab := Lab{
		ID:            "lab-1",
		SectionID:     "section-1",
		CatalogNumber: "LAB001",
		Times:         &times,
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}

	assert.Equal(t, "lab-1", lab.ID)
	assert.Equal(t, "section-1", lab.SectionID)
	assert.Equal(t, "LAB001", lab.CatalogNumber)
	assert.NotNil(t, lab.Times)
	assert.Equal(t, times, *lab.Times)
}
