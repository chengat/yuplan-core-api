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
	getRandomCourses    func(ctx context.Context, limit int) ([]models.Course, error)
	getByID             func(ctx context.Context, courseID string) (*models.Course, error)
	search              func(ctx context.Context, query string, limit, offset int) ([]models.Course, error)
	getPaginatedCourses func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error)
	getCoursesCount     func(ctx context.Context, faculty, courseCodeRange *string) (int, error)
}

func (m *MockCourseRepository) GetRandomCourses(ctx context.Context, limit int) ([]models.Course, error) {
	if m.getRandomCourses != nil {
		return m.getRandomCourses(ctx, limit)
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

func (m *MockCourseRepository) GetPaginatedCourses(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
	if m.getPaginatedCourses != nil {
		return m.getPaginatedCourses(ctx, page, pageSize, faculty, courseCodeRange)
	}
	return []models.Course{}, nil
}

func (m *MockCourseRepository) GetCoursesCount(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
	if m.getCoursesCount != nil {
		return m.getCoursesCount(ctx, faculty, courseCodeRange)
	}
	return 0, nil
}

func TestGetCourses(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getRandomCourses: func(ctx context.Context, limit int) ([]models.Course, error) {
			return []models.Course{}, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses", handler.GetCourses)

	req, _ := http.NewRequest("GET", "/courses?limit=10", nil)
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
		getRandomCourses: func(ctx context.Context, limit int) ([]models.Course, error) {
			return nil, errors.New("db down")
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.New()
	router.GET("/courses", handler.GetCourses)

	req, _ := http.NewRequest(http.MethodGet, "/courses?limit=10", nil)
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

// Tests for GetPaginatedCourses handler
func TestGetPaginatedCourses(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			return []models.Course{
				{ID: "1", Code: "EECS1000", Name: "Course 1", Faculty: "SC"},
				{ID: "2", Code: "MATH1010", Name: "Course 2", Faculty: "SC"},
			}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 100, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=1&page_size=20", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"data\"")
	assert.Contains(t, recorder.Body.String(), "\"page\":1")
	assert.Contains(t, recorder.Body.String(), "\"page_size\":20")
	assert.Contains(t, recorder.Body.String(), "\"total_items\":100")
	assert.Contains(t, recorder.Body.String(), "\"total_pages\":5")
	assert.Contains(t, recorder.Body.String(), "EECS1000")
}

func TestGetPaginatedCourses_WithDefaultValues(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			assert.Equal(t, 1, page)
			assert.Equal(t, 20, pageSize)
			return []models.Course{}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 0, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"total_pages\":1")
}

func TestGetPaginatedCourses_WithFacultyFilter(t *testing.T) {
	gin.SetMode(gin.TestMode)

	faculty := "SC"
	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, facultyFilter, courseCodeRange *string) ([]models.Course, error) {
			assert.NotNil(t, facultyFilter)
			assert.Equal(t, "SC", *facultyFilter)
			return []models.Course{
				{ID: "1", Code: "EECS1000", Name: "Course 1", Faculty: "SC"},
			}, nil
		},
		getCoursesCount: func(ctx context.Context, facultyFilter, courseCodeRange *string) (int, error) {
			assert.NotNil(t, facultyFilter)
			assert.Equal(t, "SC", *facultyFilter)
			return 50, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=1&faculty="+faculty, nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"total_items\":50")
}

func TestGetPaginatedCourses_WithCourseCodeRangeFilter(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			assert.NotNil(t, courseCodeRange)
			assert.Equal(t, "1000s", *courseCodeRange)
			return []models.Course{
				{ID: "1", Code: "EECS1000", Name: "Course 1", Faculty: "SC"},
			}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			assert.NotNil(t, courseCodeRange)
			assert.Equal(t, "1000s", *courseCodeRange)
			return 25, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=1&course_code_range=1000s", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"total_items\":25")
}

func TestGetPaginatedCourses_WithBothFilters(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			assert.NotNil(t, faculty)
			assert.NotNil(t, courseCodeRange)
			assert.Equal(t, "SC", *faculty)
			assert.Equal(t, "2000s", *courseCodeRange)
			return []models.Course{
				{ID: "1", Code: "EECS2030", Name: "Course 1", Faculty: "SC"},
			}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			assert.NotNil(t, faculty)
			assert.NotNil(t, courseCodeRange)
			return 15, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=1&faculty=SC&course_code_range=2000s", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"total_items\":15")
}

func TestGetPaginatedCourses_WithPagination(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			assert.Equal(t, 2, page)
			assert.Equal(t, 10, pageSize)
			return []models.Course{
				{ID: "11", Code: "EECS3010", Name: "Course 11", Faculty: "SC"},
			}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 100, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=2&page_size=10", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"page\":2")
	assert.Contains(t, recorder.Body.String(), "\"page_size\":10")
	assert.Contains(t, recorder.Body.String(), "\"total_pages\":10")
}

func TestGetPaginatedCourses_InvalidPageNumber_DefaultsToOne(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			assert.Equal(t, 1, page) // Should default to 1
			return []models.Course{}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 0, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=0", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
}

func TestGetPaginatedCourses_InvalidPageSize_DefaultsToTwenty(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			assert.Equal(t, 20, pageSize) // Should default to 20
			return []models.Course{}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 0, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page_size=0", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
}

func TestGetPaginatedCourses_PageSizeExceedsMax_DefaultsToTwenty(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			assert.Equal(t, 20, pageSize) // Should default to 20 (max is 100, but invalid values default to 20)
			return []models.Course{}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 0, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page_size=200", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
}

func TestGetPaginatedCourses_WhenGetCoursesCountErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 0, errors.New("db error")
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=1", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusInternalServerError, recorder.Code)
	assert.Contains(t, strings.ToLower(recorder.Body.String()), "failed")
}

func TestGetPaginatedCourses_WhenGetPaginatedCoursesErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			return nil, errors.New("db error")
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 100, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=1", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusInternalServerError, recorder.Code)
	assert.Contains(t, strings.ToLower(recorder.Body.String()), "failed")
}

func TestGetPaginatedCourses_EmptyResults(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.CourseRepositoryInterface = &MockCourseRepository{
		getPaginatedCourses: func(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
			return []models.Course{}, nil
		},
		getCoursesCount: func(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
			return 0, nil
		},
	}
	handler := NewCourseHandler(repo)

	router := gin.Default()
	router.GET("/courses/paginated", handler.GetPaginatedCourses)

	req, _ := http.NewRequest("GET", "/courses/paginated?page=1", nil)
	recorder := httptest.NewRecorder()
	router.ServeHTTP(recorder, req)

	assert.Equal(t, http.StatusOK, recorder.Code)
	assert.Contains(t, recorder.Body.String(), "\"total_items\":0")
	assert.Contains(t, recorder.Body.String(), "\"total_pages\":1")
}
