package handlers

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestSeedPipelineHandler_Post_NotConfigured(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := NewSeedPipelineHandler("", ".", "python3", false, time.Minute)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodPost, "/api/v1/admin/seed-pipeline", nil)

	h.Post(c)

	assert.Equal(t, http.StatusServiceUnavailable, w.Code)
}

func TestSeedPipelineHandler_Post_Unauthorized(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := NewSeedPipelineHandler("secret-token", ".", "python3", false, time.Minute)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodPost, "/api/v1/admin/seed-pipeline", nil)
	c.Request.Header.Set("Authorization", "Bearer wrong")

	h.Post(c)

	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestSeedPipelineHandler_Post_InvalidJSON(t *testing.T) {
	gin.SetMode(gin.TestMode)
	h := NewSeedPipelineHandler("secret-token", ".", "python3", false, time.Minute)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/admin/seed-pipeline", strings.NewReader(`not-json`))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer secret-token")
	c.Request = req

	h.Post(c)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}
