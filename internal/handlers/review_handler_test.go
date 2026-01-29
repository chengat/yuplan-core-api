package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"yuplan/internal/models"

	"github.com/gin-gonic/gin"
)

type mockReviewRepository struct {
	createFunc          func(ctx context.Context, review *models.Review) error
	getByCourseCodeFunc func(ctx context.Context, courseCode string, sortBy string, limit, offset int) ([]models.Review, error)
	getCourseStatsFunc  func(ctx context.Context, courseCode string) (map[string]interface{}, error)
}

func (m *mockReviewRepository) Create(ctx context.Context, review *models.Review) error {
	if m.createFunc != nil {
		return m.createFunc(ctx, review)
	}
	return nil
}

func (m *mockReviewRepository) GetByCourseCode(ctx context.Context, courseCode string, sortBy string, limit, offset int) ([]models.Review, error) {
	if m.getByCourseCodeFunc != nil {
		return m.getByCourseCodeFunc(ctx, courseCode, sortBy, limit, offset)
	}
	return []models.Review{}, nil
}

func (m *mockReviewRepository) GetCourseStats(ctx context.Context, courseCode string) (map[string]interface{}, error) {
	if m.getCourseStatsFunc != nil {
		return m.getCourseStatsFunc(ctx, courseCode)
	}
	return map[string]interface{}{
		"total_reviews":            0,
		"likes":                    0,
		"dislikes":                 0,
		"like_percentage":          0,
		"avg_difficulty":           0.0,
		"avg_real_world_relevance": 0.0,
	}, nil
}

func TestCreateReview(t *testing.T) {
	gin.SetMode(gin.TestMode)

	authorName := "John Smith"
	tests := []struct {
		name           string
		courseCode     string
		requestBody    interface{}
		mockError      error
		expectedStatus int
	}{
		{
			name:       "Valid review with name",
			courseCode: "EECS2030",
			requestBody: models.CreateReviewRequest{
				Email:              "student@yorku.ca",
				AuthorName:         &authorName,
				Liked:              true,
				Difficulty:         3,
				RealWorldRelevance: 5,
			},
			mockError:      nil,
			expectedStatus: http.StatusCreated,
		},
		{
			name:       "Valid anonymous review",
			courseCode: "EECS2030",
			requestBody: models.CreateReviewRequest{
				Email:              "student@yorku.ca",
				AuthorName:         nil,
				Liked:              true,
				Difficulty:         3,
				RealWorldRelevance: 5,
			},
			mockError:      nil,
			expectedStatus: http.StatusCreated,
		},
		{
			name:       "Invalid email",
			courseCode: "EECS2030",
			requestBody: map[string]interface{}{
				"email":                "not-an-email",
				"liked":                true,
				"difficulty":           3,
				"real_world_relevance": 5,
			},
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:       "Invalid difficulty",
			courseCode: "EECS2030",
			requestBody: map[string]interface{}{
				"email":                "student@yorku.ca",
				"liked":                true,
				"difficulty":           6,
				"real_world_relevance": 5,
			},
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:       "Invalid real_world_relevance",
			courseCode: "EECS2030",
			requestBody: map[string]interface{}{
				"email":                "student@yorku.ca",
				"liked":                true,
				"difficulty":           3,
				"real_world_relevance": 0,
			},
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockReviewRepo := &mockReviewRepository{
				createFunc: func(ctx context.Context, review *models.Review) error {
					review.ID = "test-review-id"
					return tt.mockError
				},
			}

			handler := NewReviewHandler(mockReviewRepo)

			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)

			body, _ := json.Marshal(tt.requestBody)
			req := httptest.NewRequest("POST", "/api/v1/courses/"+tt.courseCode+"/reviews", bytes.NewBuffer(body))
			req.Header.Set("Content-Type", "application/json")
			c.Request = req
			c.Params = gin.Params{{Key: "course_code", Value: tt.courseCode}}

			handler.CreateReview(c)

			if w.Code != tt.expectedStatus {
				t.Errorf("Expected status %d, got %d. Body: %s", tt.expectedStatus, w.Code, w.Body.String())
			}

			if w.Code == http.StatusCreated {
				var response map[string]interface{}
				if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
					t.Fatalf("Failed to unmarshal response: %v", err)
				}

				if _, ok := response["data"]; !ok {
					t.Error("Expected 'data' in response")
				}
				if _, ok := response["message"]; !ok {
					t.Error("Expected 'message' in response")
				}
			}
		})
	}
}

func TestGetReviews(t *testing.T) {
	gin.SetMode(gin.TestMode)

	reviewText := "Great course!"
	authorName := "John Smith"
	mockReviews := []models.Review{
		{
			ID:                 "review-1",
			CourseCode:         "EECS2030",
			Email:              "student@yorku.ca",
			AuthorName:         &authorName,
			Liked:              true,
			Difficulty:         3,
			RealWorldRelevance: 5,
			ReviewText:         &reviewText,
		},
	}

	mockStats := map[string]interface{}{
		"total_reviews":            10,
		"likes":                    7,
		"dislikes":                 3,
		"like_percentage":          70,
		"avg_difficulty":           3.5,
		"avg_real_world_relevance": 4.2,
	}

	tests := []struct {
		name           string
		courseCode     string
		queryParams    string
		expectedStatus int
	}{
		{
			name:           "Get reviews with default params",
			courseCode:     "EECS2030",
			queryParams:    "",
			expectedStatus: http.StatusOK,
		},
		{
			name:           "Get reviews sorted by recent",
			courseCode:     "EECS2030",
			queryParams:    "?sort=recent&limit=10&offset=0",
			expectedStatus: http.StatusOK,
		},
		{
			name:           "Get reviews sorted by earliest",
			courseCode:     "EECS2030",
			queryParams:    "?sort=earliest&limit=20&offset=10",
			expectedStatus: http.StatusOK,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockReviewRepo := &mockReviewRepository{
				getByCourseCodeFunc: func(ctx context.Context, courseCode string, sortBy string, limit, offset int) ([]models.Review, error) {
					return mockReviews, nil
				},
				getCourseStatsFunc: func(ctx context.Context, courseCode string) (map[string]interface{}, error) {
					return mockStats, nil
				},
			}

			handler := NewReviewHandler(mockReviewRepo)

			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)

			req := httptest.NewRequest("GET", "/api/v1/courses/"+tt.courseCode+"/reviews"+tt.queryParams, nil)
			c.Request = req
			c.Params = gin.Params{{Key: "course_code", Value: tt.courseCode}}

			handler.GetReviews(c)

			if w.Code != tt.expectedStatus {
				t.Errorf("Expected status %d, got %d. Body: %s", tt.expectedStatus, w.Code, w.Body.String())
			}

			if w.Code == http.StatusOK {
				var response map[string]interface{}
				if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
					t.Fatalf("Failed to unmarshal response: %v", err)
				}

				if _, ok := response["data"]; !ok {
					t.Error("Expected 'data' in response")
				}
				if _, ok := response["count"]; !ok {
					t.Error("Expected 'count' in response")
				}
				if _, ok := response["stats"]; !ok {
					t.Error("Expected 'stats' in response")
				}

				stats := response["stats"].(map[string]interface{})
				if stats["total_reviews"].(float64) != 10 {
					t.Errorf("Expected total_reviews 10, got %v", stats["total_reviews"])
				}
			}
		})
	}
}
