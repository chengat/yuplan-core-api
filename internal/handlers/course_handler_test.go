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
	getAllRandomized func(ctx context.Context, limit, offset int) ([]models.Course, error)
	getByID          func(ctx context.Context, courseID string) (*models.Course, error)
	search           func(ctx context.Context, query string, limit, offset int) ([]models.Course, error)
}

func (m *MockCourseRepository) GetAllRandomized(ctx context.Context, limit, offset int) ([]models.Course, error) {
	if m.getAllRandomized != nil {
		return m.getAllRandomized(ctx, limit, offset)
	}
	return []models.Course{}, nil
}

func (m *MockCourseRepository) GetByID(ctx context.Context, courseID string) (*models.Course, error) {
	if m.getByID != nil {
		return m.getByID(ctx, courseID)
	}
	return &models.Course{}, nil
}

func (m *MockCourseRepository) Search(ctx context.Context, query string, limit, offset int) ([]models.Course, error) {
	if m.search != nil {
		return m.search(ctx, query, limit, offset)
	}
	return []models.Course{}, nil
}

func TestGetCourses(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getAllRandomized: func(ctx context.Context, limit, offset int) ([]models.Course, error) {
			return []models.Course{}, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses", handler.GetCourses)

	req, _ := http.NewRequest("GET", "/courses?limit=10&offset=0", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"data\"")
	assert.Contains(t, recorder.Body.String(), "\"count\"")
}

func TestGetCourseByID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getByID: func(ctx context.Context, courseID string) (*models.Course, error) {
			return &models.Course{ID: courseID}, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/:course_id", handler.GetCourseByID)

	req, _ := http.NewRequest("GET", "/courses/test-id", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"data\"")
	assert.Contains(t, recorder.Body.String(), "test-id")
}

func TestGetCourses_WhenRepoErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getAllRandomized: func(ctx context.Context, limit, offset int) ([]models.Course, error) {
			return nil, errors.New("db down")
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.New()
	router.GET("/courses", handler.GetCourses)

	req, _ := http.NewRequest(http.MethodGet, "/courses?limit=10&offset=0", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusInternalServerError, recorder.Code)
	assert.Contains(t, strings.ToLower(recorder.Body.String()), "failed")
}

func TestGetCourseByID_WhenRepoErrors_Returns404(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getByID: func(ctx context.Context, courseID string) (*models.Course, error) {
			return nil, errors.New("not found")
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.New()
	router.GET("/courses/:course_id", handler.GetCourseByID)

	req, _ := http.NewRequest(http.MethodGet, "/courses/test-id", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusNotFound, recorder.Code)
	assert.Contains(t, strings.ToLower(recorder.Body.String()), "not found")
}

func TestSearchCourses(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		search: func(ctx context.Context, query string, limit, offset int) ([]models.Course, error) {
			return []models.Course{
				{ID: "1", Code: "EECS3311", Name: "Software Design"},
				{ID: "2", Code: "EECS4313", Name: "Software Engineering"},
			}, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/search", handler.SearchCourses)

	req, _ := http.NewRequest("GET", "/courses/search?q=EECS", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"data\"")
	assert.Contains(t, recorder.Body.String(), "\"count\"")
	assert.Contains(t, recorder.Body.String(), "EECS3311")
	assert.Contains(t, recorder.Body.String(), "Software Design")
}

func TestSearchCourses_WithPagination(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		search: func(ctx context.Context, query string, limit, offset int) ([]models.Course, error) {
			assert.Equal(t, "Software", query)
			assert.Equal(t, 10, limit)
			assert.Equal(t, 5, offset)
			return []models.Course{
				{ID: "1", Code: "EECS3311", Name: "Software Design"},
			}, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/search", handler.SearchCourses)

	req, _ := http.NewRequest("GET", "/courses/search?q=Software&limit=10&offset=5", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "Software Design")
}

func TestSearchCourses_MissingQueryParam_Returns400(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/search", handler.SearchCourses)

	req, _ := http.NewRequest("GET", "/courses/search", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusBadRequest, recorder.Code)
	assert.Contains(t, strings.ToLower(recorder.Body.String()), "required")
}

func TestSearchCourses_WhenRepoErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		search: func(ctx context.Context, query string, limit, offset int) ([]models.Course, error) {
			return nil, errors.New("db error")
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/search", handler.SearchCourses)

	req, _ := http.NewRequest("GET", "/courses/search?q=EECS", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusInternalServerError, recorder.Code)
	assert.Contains(t, strings.ToLower(recorder.Body.String()), "failed")
}

func TestSearchCourses_EmptyResults(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		search: func(ctx context.Context, query string, limit, offset int) ([]models.Course, error) {
			return []models.Course{}, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/search", handler.SearchCourses)

	req, _ := http.NewRequest("GET", "/courses/search?q=NONEXISTENT", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"count\":0")
}
