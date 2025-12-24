package handlers

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
	"yuplan/internal/models"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

type MockInstructorRepository struct {
	getByCourseID func(ctx context.Context, courseID string) ([]models.Instructor, error)
}

func (m *MockInstructorRepository) GetByCourseID(ctx context.Context, courseID string) ([]models.Instructor, error) {
	if m.getByCourseID != nil {
		return m.getByCourseID(ctx, courseID)
	}
	return []models.Instructor{}, nil
}

func TestGetInstructorsByCourseID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	rmpLink := "https://www.ratemyprofessors.com/search/professors/?q=John+Doe"
	sectionID := "section-1"
	
	var repo repository.InstructorRepositoryInterface = &MockInstructorRepository{
		getByCourseID: func(ctx context.Context, courseID string) ([]models.Instructor, error) {
			return []models.Instructor{
				{
					ID:             "instructor-1",
					FirstName:      "John",
					LastName:       "Doe",
					RateMyProfLink: &rmpLink,
					SectionID:      &sectionID,
					CreatedAt:      time.Now(),
					UpdatedAt:      time.Now(),
				},
				{
					ID:        "instructor-2",
					FirstName: "Jane",
					LastName:  "Smith",
					SectionID: &sectionID,
					CreatedAt: time.Now(),
					UpdatedAt: time.Now(),
				},
			}, nil
		},
	}
	handler := NewInstructorHandler(repo)

	r := gin.Default()
	r.GET("/instructors/:course_id", handler.GetInstructorsByCourseID)

	req, _ := http.NewRequest("GET", "/instructors/course-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
	assert.Contains(t, w.Body.String(), "instructor-1")
	assert.Contains(t, w.Body.String(), "instructor-2")
	assert.Contains(t, w.Body.String(), "John")
	assert.Contains(t, w.Body.String(), "Doe")
	assert.Contains(t, w.Body.String(), "Jane")
	assert.Contains(t, w.Body.String(), "Smith")
	assert.Contains(t, w.Body.String(), "\"count\":2")
}

func TestGetInstructorsByCourseID_EmptyResult(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.InstructorRepositoryInterface = &MockInstructorRepository{
		getByCourseID: func(ctx context.Context, courseID string) ([]models.Instructor, error) {
			return []models.Instructor{}, nil
		},
	}
	handler := NewInstructorHandler(repo)

	r := gin.Default()
	r.GET("/instructors/:course_id", handler.GetInstructorsByCourseID)

	req, _ := http.NewRequest("GET", "/instructors/course-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
	assert.Contains(t, w.Body.String(), "[]")
	assert.Contains(t, w.Body.String(), "\"count\":0")
}

func TestGetInstructorsByCourseID_WhenRepoErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.InstructorRepositoryInterface = &MockInstructorRepository{
		getByCourseID: func(ctx context.Context, courseID string) ([]models.Instructor, error) {
			return nil, errors.New("db error")
		},
	}
	handler := NewInstructorHandler(repo)

	r := gin.New()
	r.GET("/instructors/:course_id", handler.GetInstructorsByCourseID)

	req, _ := http.NewRequest(http.MethodGet, "/instructors/course-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, strings.ToLower(w.Body.String()), "failed")
}

