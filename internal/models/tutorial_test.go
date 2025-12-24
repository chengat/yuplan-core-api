package models

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestTutorialModel(t *testing.T) {
	times := `[{"day": "M", "time": "10:30", "duration": "110"}]`
	tutorial := Tutorial{
		ID:            "tutorial-1",
		SectionID:     "section-1",
		CatalogNumber: "TUT01",
		Times:         &times,
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}

	assert.Equal(t, "tutorial-1", tutorial.ID)
	assert.Equal(t, "section-1", tutorial.SectionID)
	assert.Equal(t, "TUT01", tutorial.CatalogNumber)
	assert.NotNil(t, tutorial.Times)
	assert.Equal(t, times, *tutorial.Times)
}
