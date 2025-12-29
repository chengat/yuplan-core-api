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

type MockSectionRepository struct {
	getByCourseID func(ctx context.Context, courseID string) ([]models.Section, error)
}

func (m *MockSectionRepository) GetByCourseID(ctx context.Context, courseID string) ([]models.Section, error) {
	if m.getByCourseID != nil {
		return m.getByCourseID(ctx, courseID)
	}
	return []models.Section{}, nil
}

func TestGetSectionsByCourseID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.SectionRepositoryInterface = &MockSectionRepository{
		getByCourseID: func(ctx context.Context, courseID string) ([]models.Section, error) {
			return []models.Section{
				{
					ID:        "section-1",
					CourseID:  courseID,
					Letter:    "A",
					CreatedAt: time.Now(),
					UpdatedAt: time.Now(),
				},
				{
					ID:        "section-2",
					CourseID:  courseID,
					Letter:    "B",
					CreatedAt: time.Now(),
					UpdatedAt: time.Now(),
				},
			}, nil
		},
	}
	handler := NewSectionHandler(repo)

	r := gin.Default()
	r.GET("/section/:course_id", handler.GetSectionsByCourseID)

	req, _ := http.NewRequest("GET", "/section/course-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
	assert.Contains(t, w.Body.String(), "section-1")
	assert.Contains(t, w.Body.String(), "section-2")
	assert.Contains(t, w.Body.String(), "\"count\":2")
}

func TestGetSectionsByCourseID_EmptyResult(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.SectionRepositoryInterface = &MockSectionRepository{
		getByCourseID: func(ctx context.Context, courseID string) ([]models.Section, error) {
			return []models.Section{}, nil
		},
	}
	handler := NewSectionHandler(repo)

	r := gin.Default()
	r.GET("/section/:course_id", handler.GetSectionsByCourseID)

	req, _ := http.NewRequest("GET", "/section/course-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
	assert.Contains(t, w.Body.String(), "[]")
	assert.Contains(t, w.Body.String(), "\"count\":0")
}

func TestGetSectionsByCourseID_WhenRepoErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.SectionRepositoryInterface = &MockSectionRepository{
		getByCourseID: func(ctx context.Context, courseID string) ([]models.Section, error) {
			return nil, errors.New("db error")
		},
	}
	handler := NewSectionHandler(repo)

	r := gin.New()
	r.GET("/section/:course_id", handler.GetSectionsByCourseID)

	req, _ := http.NewRequest(http.MethodGet, "/section/course-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, strings.ToLower(w.Body.String()), "failed")
}
