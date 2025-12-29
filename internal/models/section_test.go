package models

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestSectionModel(t *testing.T) {
    section := Section{
        ID:        "section-1",
        CourseID:  "course-1",
        Letter:    "A",
        CreatedAt: time.Now(),
        UpdatedAt: time.Now(),
    }

    assert.Equal(t, "section-1", section.ID)
    assert.Equal(t, "course-1", section.CourseID)
    assert.Equal(t, "A", section.Letter)
}