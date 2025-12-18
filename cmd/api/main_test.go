package main

import (
	"context"
	"net/http"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestSetupRouter_RegistersCourseRoutes(t *testing.T) {
	// Passing nil is OK here: setupRouter only wires dependencies.
	// We won't execute any handlers that require a real database.
	r := setupRouter(nil)

	routes := r.Routes()
	assert.NotEmpty(t, routes)

	seen := map[string]bool{}
	for _, rt := range routes {
		seen[rt.Method+" "+rt.Path] = true
	}

	assert.True(t, seen[http.MethodGet+" /api/v1/courses"], "expected GET /api/v1/courses route")
	assert.True(t, seen[http.MethodGet+" /api/v1/courses/:course_id"], "expected GET /api/v1/courses/:course_id route")
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
