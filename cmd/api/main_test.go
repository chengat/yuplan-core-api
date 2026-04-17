package main

import (
	"context"
	"net/http"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"yuplan/internal/config"
)

func TestSetupRouter_RegistersCourseRoutes(t *testing.T) {
	// Passing nil is OK here: setupRouter only wires dependencies.
	// We won't execute any handlers that require a real database.
	r := setupRouter(nil, &config.Config{})

	routes := r.Routes()
	assert.NotEmpty(t, routes)

	seen := map[string]bool{}
	for _, rt := range routes {
		seen[rt.Method+" "+rt.Path] = true
	}

	assert.True(t, seen[http.MethodGet+" /api/v1/courses"], "expected GET /api/v1/courses route")
	assert.True(t, seen[http.MethodGet+" /api/v1/courses/search"], "expected GET /api/v1/courses/search route")
	assert.True(t, seen[http.MethodGet+" /api/v1/courses/:course_code"], "expected GET /api/v1/courses/:course_code route")
	assert.True(t, seen[http.MethodPost+" /api/v1/admin/seed/pipeline"], "expected POST /api/v1/admin/seed/pipeline route")
}

func TestInitDatabase_InvalidURL_ReturnsError(t *testing.T) {
	pool, err := initDatabase(context.Background(), "://not-a-valid-url")
	assert.Error(t, err)
	assert.Nil(t, pool)
}

func TestStartServer_InvalidPort_ReturnsError(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()

	err := startServer(r, "not-a-number")
	assert.Error(t, err)
}
