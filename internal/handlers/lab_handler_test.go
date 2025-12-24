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

type MockLabRepository struct {
	getBySectionID func(ctx context.Context, sectionID string) ([]models.Lab, error)
}

func (m *MockLabRepository) GetBySectionID(ctx context.Context, sectionID string) ([]models.Lab, error) {
	if m.getBySectionID != nil {
		return m.getBySectionID(ctx, sectionID)
	}
	return []models.Lab{}, nil
}

func TestGetLabsBySectionID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	times := `[{"day": "M", "time": "10:30", "duration": "110"}]`
	var repo repository.LabRepositoryInterface = &MockLabRepository{
		getBySectionID: func(ctx context.Context, sectionID string) ([]models.Lab, error) {
			return []models.Lab{
				{
					ID:            "lab-1",
					SectionID:     sectionID,
					CatalogNumber: "LAB001",
					Times:         &times,
					CreatedAt:     time.Now(),
					UpdatedAt:     time.Now(),
				},
			}, nil
		},
	}
	handler := NewLabHandler(repo)

	r := gin.Default()
	r.GET("/labs/:section_id", handler.GetLabsBySectionID)

	req, _ := http.NewRequest("GET", "/labs/section-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
	assert.Contains(t, w.Body.String(), "lab-1")
	assert.Contains(t, w.Body.String(), "LAB001")
}

func TestGetLabsBySectionID_EmptyResult(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.LabRepositoryInterface = &MockLabRepository{
		getBySectionID: func(ctx context.Context, sectionID string) ([]models.Lab, error) {
			return []models.Lab{}, nil
		},
	}
	handler := NewLabHandler(repo)

	r := gin.Default()
	r.GET("/labs/:section_id", handler.GetLabsBySectionID)

	req, _ := http.NewRequest("GET", "/labs/section-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "\"data\"")
	assert.Contains(t, w.Body.String(), "\"count\"")
	assert.Contains(t, w.Body.String(), "[]")
	assert.Contains(t, w.Body.String(), "\"count\":0")
}

func TestGetLabsBySectionID_WhenRepoErrors_Returns500(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var repo repository.LabRepositoryInterface = &MockLabRepository{
		getBySectionID: func(ctx context.Context, sectionID string) ([]models.Lab, error) {
			return nil, errors.New("db error")
		},
	}
	handler := NewLabHandler(repo)

	r := gin.New()
	r.GET("/labs/:section_id", handler.GetLabsBySectionID)

	req, _ := http.NewRequest(http.MethodGet, "/labs/section-1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, strings.ToLower(w.Body.String()), "failed")
}
