package handlers

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"yuplan/internal/models"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

type MockCourseRepository struct {
	getAll  func(ctx context.Context, limit, offset int) ([]models.Course, error)
	getByID func(ctx context.Context, courseID string) (*models.Course, error)
}

func (m *MockCourseRepository) GetAll(ctx context.Context, limit, offset int) ([]models.Course, error) {
	if m.getAll != nil {
		return m.getAll(ctx, limit, offset)
	}
	return []models.Course{}, nil
}

func (m *MockCourseRepository) GetByID(ctx context.Context, courseID string) (*models.Course, error) {
	if m.getByID != nil {
		return m.getByID(ctx, courseID)
	}
	return &models.Course{}, nil
}

func TestGetCourses(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getAll: func(ctx context.Context, limit, offset int) ([]models.Course, error) {
			return []models.Course{}, nil
		},
	}
	handler := NewCourseHandler(repo)

	r := gin.Default()
	r.GET("/courses", handler.GetCourses)

	req, _ := http.NewRequest("GET", "/courses?limit=10&offset=0", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
}

func TestGetCourseByID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getByID: func(ctx context.Context, courseID string) (*models.Course, error) {
			return &models.Course{ID: courseID}, nil
		},
	}
	handler := NewCourseHandler(repo)

	r := gin.Default()
	r.GET("/courses/:course_id", handler.GetCourseByID)

	req, _ := http.NewRequest("GET", "/courses/test-id", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "test-id")
}

func TestGetCourses_WhenRepoErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getAll: func(ctx context.Context, limit, offset int) ([]models.Course, error) {
			return nil, errors.New("db down")
		},
	}
	handler := NewCourseHandler(repo)

	r := gin.New()
	r.GET("/courses", handler.GetCourses)

	req, _ := http.NewRequest(http.MethodGet, "/courses?limit=10&offset=0", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, strings.ToLower(w.Body.String()), "failed")
}

func TestGetCourseByID_WhenRepoErrors_Returns404(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getByID: func(ctx context.Context, courseID string) (*models.Course, error) {
			return nil, errors.New("not found")
		},
	}
	handler := NewCourseHandler(repo)

	r := gin.New()
	r.GET("/courses/:course_id", handler.GetCourseByID)

	req, _ := http.NewRequest(http.MethodGet, "/courses/test-id", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotFound, w.Code)
	assert.Contains(t, strings.ToLower(w.Body.String()), "not found")
}
