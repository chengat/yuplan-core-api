package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestRateLimiter_AllowsRequestsWithinLimit(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	limiter := NewRateLimiter(5, 1*time.Minute)
	
	router := gin.New()
	router.Use(limiter.Limit())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "ok"})
	})
	
	// Make 5 requests (should all succeed)
	for i := 0; i < 5; i++ {
		w := httptest.NewRecorder()
		req := httptest.NewRequest("GET", "/test", nil)
		req.RemoteAddr = "192.168.1.1:1234"
		router.ServeHTTP(w, req)
		
		assert.Equal(t, http.StatusOK, w.Code, "Request %d should succeed", i+1)
	}
}

func TestRateLimiter_BlocksRequestsOverLimit(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	limiter := NewRateLimiter(3, 1*time.Minute)
	
	router := gin.New()
	router.Use(limiter.Limit())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "ok"})
	})
	
	// Make 3 requests (should succeed)
	for i := 0; i < 3; i++ {
		w := httptest.NewRecorder()
		req := httptest.NewRequest("GET", "/test", nil)
		req.RemoteAddr = "192.168.1.1:1234"
		router.ServeHTTP(w, req)
		
		assert.Equal(t, http.StatusOK, w.Code, "Request %d should succeed", i+1)
	}
	
	// 4th request should be blocked
	w := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/test", nil)
	req.RemoteAddr = "192.168.1.1:1234"
	router.ServeHTTP(w, req)
	
	assert.Equal(t, http.StatusTooManyRequests, w.Code, "4th request should be blocked")
}

func TestRateLimiter_DifferentIPsHaveSeparateLimits(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	limiter := NewRateLimiter(2, 1*time.Minute)
	
	router := gin.New()
	router.Use(limiter.Limit())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "ok"})
	})
	
	// IP 1: Make 2 requests (hit limit)
	for i := 0; i < 2; i++ {
		w := httptest.NewRecorder()
		req := httptest.NewRequest("GET", "/test", nil)
		req.RemoteAddr = "192.168.1.1:1234"
		router.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code)
	}
	
	// IP 1: 3rd request blocked
	w := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/test", nil)
	req.RemoteAddr = "192.168.1.1:1234"
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusTooManyRequests, w.Code)
	
	// IP 2: Should still work (different IP)
	w = httptest.NewRecorder()
	req = httptest.NewRequest("GET", "/test", nil)
	req.RemoteAddr = "192.168.1.2:1234"
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusOK, w.Code, "Different IP should have its own limit")
}

func TestRateLimiter_ResetsAfterWindow(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	// Short window for testing (100ms)
	limiter := NewRateLimiter(2, 100*time.Millisecond)
	
	router := gin.New()
	router.Use(limiter.Limit())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "ok"})
	})
	
	// Make 2 requests (hit limit)
	for i := 0; i < 2; i++ {
		w := httptest.NewRecorder()
		req := httptest.NewRequest("GET", "/test", nil)
		req.RemoteAddr = "192.168.1.1:1234"
		router.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code)
	}
	
	// 3rd request blocked
	w := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/test", nil)
	req.RemoteAddr = "192.168.1.1:1234"
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusTooManyRequests, w.Code)
	
	// Wait for window to reset
	time.Sleep(150 * time.Millisecond)
	
	// Should work again after reset
	w = httptest.NewRecorder()
	req = httptest.NewRequest("GET", "/test", nil)
	req.RemoteAddr = "192.168.1.1:1234"
	router.ServeHTTP(w, req)
	assert.Equal(t, http.StatusOK, w.Code, "Should work after window reset")
}
