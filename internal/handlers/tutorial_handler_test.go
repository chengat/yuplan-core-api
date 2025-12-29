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

type MockTutorialRepository struct {
	getBySectionID func(ctx context.Context, sectionID string) ([]models.Tutorial, error)
}

func (m *MockTutorialRepository) GetBySectionID(ctx context.Context, sectionID string) ([]models.Tutorial, error) {
	if m.getBySectionID != nil {
		return m.getBySectionID(ctx, sectionID)
	}
	return []models.Tutorial{}, nil
}

func TestGetTutorialsBySectionID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	times := `[{"day": "M", "time": "10:30", "duration": "110"}]`
	var repo repository.TutorialRepositoryInterface = &MockTutorialRepository{
		getBySectionID: func(ctx context.Context, sectionID string) ([]models.Tutorial, error) {
			return []models.Tutorial{
				{
					ID:            "tutorial-1",
					SectionID:     sectionID,
					CatalogNumber: "TUTR01",
					Times:         &times,
					CreatedAt:     time.Now(),
					UpdatedAt:     time.Now(),
				},
			}, nil
		},
	}
	handler := NewTutorialHandler(repo)
	r := gin.Default()
	r.GET("/tutorial/:section_id", handler.GetTutorialsBySectionID)

	req, _ := http.NewRequest("GET", "/tutorial/section-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
	assert.Contains(t, w.Body.String(), "tutorial-1")
	assert.Contains(t, w.Body.String(), "TUTR01")
}

func TestGetTutorialsBySectionID_EmptyResult(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.TutorialRepositoryInterface = &MockTutorialRepository{
		getBySectionID: func(ctx context.Context, sectionID string) ([]models.Tutorial, error) {
			return []models.Tutorial{}, nil
		},
	}
	handler := NewTutorialHandler(repo)

	r := gin.Default()
	r.GET("/tutorial/:section_id", handler.GetTutorialsBySectionID)

	req, _ := http.NewRequest("GET", "/tutorial/section-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
	assert.Contains(t, w.Body.String(), "[]")
	assert.Contains(t, w.Body.String(), "\"count\":0")
}

func TestGetTutorialsBySectionID_WhenRepoErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.TutorialRepositoryInterface = &MockTutorialRepository{
		getBySectionID: func(ctx context.Context, sectionID string) ([]models.Tutorial, error) {
			return nil, errors.New("db error")
		},
	}
	handler := NewTutorialHandler(repo)
	r := gin.New()
	r.GET("/tutorial/:section_id", handler.GetTutorialsBySectionID)

	req, _ := http.NewRequest(http.MethodGet, "/tutorial/section-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, strings.ToLower(w.Body.String()), "failed")
}
