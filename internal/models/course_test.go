package models

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestCourseModel(t *testing.T) {
	course := Course{
		ID:          "1",
		Name:        "Test Course",
		Code:        "TC101",
		Credits:     3.0,
		Faculty:     "SC",
		Term:        "Fall",
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	assert.Equal(t, "1", course.ID)
	assert.Equal(t, "Test Course", course.Name)
	assert.Equal(t, "TC101", course.Code)
	assert.Equal(t, 3.0, course.Credits)
	assert.Equal(t, "SC", course.Faculty)
	assert.Equal(t, "Fall", course.Term)
}
