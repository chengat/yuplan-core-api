package middleware

import (
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestResponseCache_SecondHitUsesStore(t *testing.T) {
	gin.SetMode(gin.TestMode)
	store := NewResponseCacheStore()
	var calls atomic.Int32

	r := gin.New()
	r.GET("/x", CatalogHTTPCache(store, time.Minute, time.Hour), func(c *gin.Context) {
		calls.Add(1)
		c.JSON(http.StatusOK, gin.H{"n": int(calls.Load())})
	})

	req := httptest.NewRequest(http.MethodGet, "/x", nil)
	w1 := httptest.NewRecorder()
	r.ServeHTTP(w1, req)
	assert.Equal(t, http.StatusOK, w1.Code)
	assert.Contains(t, w1.Body.String(), `"n":1`)
	assert.Equal(t, int32(1), calls.Load())
	assert.Contains(t, w1.Header().Get("Cache-Control"), "max-age=60")
	assert.NotEmpty(t, w1.Header().Get("ETag"))
	assert.NotEmpty(t, w1.Header().Get("Last-Modified"))

	w2 := httptest.NewRecorder()
	r.ServeHTTP(w2, httptest.NewRequest(http.MethodGet, "/x", nil))
	assert.Equal(t, http.StatusOK, w2.Code)
	assert.Contains(t, w2.Body.String(), `"n":1`)
	assert.Equal(t, int32(1), calls.Load(), "handler should not run on cache hit")
	assert.Contains(t, w2.Header().Get("Cache-Control"), "max-age=60")
	assert.NotEmpty(t, w2.Header().Get("ETag"))
	assert.NotEmpty(t, w2.Header().Get("Last-Modified"))
}

func TestResponseCache_DifferentQueryDifferentEntry(t *testing.T) {
	gin.SetMode(gin.TestMode)
	store := NewResponseCacheStore()
	var calls atomic.Int32

	r := gin.New()
	r.GET("/q", CatalogHTTPCache(store, time.Minute, time.Hour), func(c *gin.Context) {
		calls.Add(1)
		c.JSON(http.StatusOK, gin.H{"q": c.Query("a")})
	})

	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/q?a=1", nil))
	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/q?a=2", nil))
	assert.Equal(t, int32(2), calls.Load())
}

func TestResponseCache_RepeatedQueryParamsHaveDistinctKeys(t *testing.T) {
	gin.SetMode(gin.TestMode)
	store := NewResponseCacheStore()
	var calls atomic.Int32

	r := gin.New()
	r.GET("/q", CatalogHTTPCache(store, time.Minute, time.Hour), func(c *gin.Context) {
		calls.Add(1)
		c.JSON(http.StatusOK, gin.H{"a": c.QueryArray("a")})
	})

	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/q?a=1&a=2", nil))
	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/q?a=1", nil))
	assert.Equal(t, int32(2), calls.Load())
}

func TestCatalogHTTPCache_Returns304WithIfNoneMatch(t *testing.T) {
	gin.SetMode(gin.TestMode)
	store := NewResponseCacheStore()

	r := gin.New()
	r.GET("/catalog", CatalogHTTPCache(store, time.Minute, time.Hour), func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"ok": true})
	})

	w1 := httptest.NewRecorder()
	r.ServeHTTP(w1, httptest.NewRequest(http.MethodGet, "/catalog", nil))
	etag := w1.Header().Get("ETag")
	assert.NotEmpty(t, etag)

	req2 := httptest.NewRequest(http.MethodGet, "/catalog", nil)
	req2.Header.Set("If-None-Match", etag)
	w2 := httptest.NewRecorder()
	r.ServeHTTP(w2, req2)

	assert.Equal(t, http.StatusNotModified, w2.Code)
	assert.Empty(t, w2.Body.String())
}

func TestNoStore_SetsHeader(t *testing.T) {
	gin.SetMode(gin.TestMode)

	r := gin.New()
	r.GET("/reviews", NoStore(), func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"ok": true})
	})

	w := httptest.NewRecorder()
	r.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/reviews", nil))
	assert.Equal(t, "no-store", w.Header().Get("Cache-Control"))
}

func TestCatalogHTTPCache_EvictsWhenMaxEntriesExceeded(t *testing.T) {
	gin.SetMode(gin.TestMode)
	store := NewResponseCacheStore()
	store.maxEntries = 2

	r := gin.New()
	r.GET("/q", CatalogHTTPCache(store, time.Minute, time.Hour), func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"q": c.Query("k")})
	})

	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/q?k=1", nil))
	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/q?k=2", nil))
	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/q?k=3", nil))

	store.mu.RLock()
	defer store.mu.RUnlock()
	assert.LessOrEqual(t, len(store.data), 2)
}
