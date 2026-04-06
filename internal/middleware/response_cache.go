package middleware

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

const defaultMaxCacheEntries = 2000

type cachedResponse struct {
	status      int
	contentType string
	body        []byte
	eTag        string
	lastMod     time.Time
	expires     time.Time
}

// ResponseCacheStore holds cached HTTP response bodies for GET handlers.
type ResponseCacheStore struct {
	mu         sync.RWMutex
	data       map[string]cachedResponse
	maxEntries int
}

// NewResponseCacheStore creates an empty cache.
func NewResponseCacheStore() *ResponseCacheStore {
	return &ResponseCacheStore{
		data:       make(map[string]cachedResponse),
		maxEntries: defaultMaxCacheEntries,
	}
}

func cacheKey(c *gin.Context) string {
	q := c.Request.URL.Query()
	keys := make([]string, 0, len(q))
	for k := range q {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var b strings.Builder
	b.WriteString(c.Request.Method)
	b.WriteByte(' ')
	b.WriteString(c.Request.URL.Path)
	if len(keys) > 0 {
		b.WriteByte('?')
		pairIndex := 0
		for _, k := range keys {
			vals := q[k]
			if len(vals) == 0 {
				if pairIndex > 0 {
					b.WriteByte('&')
				}
				b.WriteString(url.QueryEscape(k))
				b.WriteByte('=')
				pairIndex++
				continue
			}
			for _, v := range vals {
				if pairIndex > 0 {
					b.WriteByte('&')
				}
				b.WriteString(url.QueryEscape(k))
				b.WriteByte('=')
				b.WriteString(url.QueryEscape(v))
				pairIndex++
			}
		}
	}
	return b.String()
}

type responseCaptureWriter struct {
	gin.ResponseWriter
	orig   gin.ResponseWriter
	header http.Header
	body   *bytes.Buffer
	status int
	size   int
}

func newResponseCaptureWriter(orig gin.ResponseWriter) *responseCaptureWriter {
	return &responseCaptureWriter{
		ResponseWriter: orig,
		orig:           orig,
		header:         make(http.Header),
		body:           &bytes.Buffer{},
		status:         0,
		size:           -1,
	}
}

func (w *responseCaptureWriter) Header() http.Header {
	return w.header
}

func (w *responseCaptureWriter) WriteHeader(code int) {
	w.status = code
}

func (w *responseCaptureWriter) Write(b []byte) (int, error) {
	if w.status == 0 {
		w.status = http.StatusOK
	}
	if w.size < 0 {
		w.size = 0
	}
	w.body.Write(b)
	w.size += len(b)
	return len(b), nil
}

func (w *responseCaptureWriter) WriteString(s string) (int, error) {
	return w.Write([]byte(s))
}

func (w *responseCaptureWriter) Status() int {
	if w.status == 0 {
		return http.StatusOK
	}
	return w.status
}

func (w *responseCaptureWriter) Size() int {
	return w.size
}

func (w *responseCaptureWriter) Written() bool {
	return w.size >= 0 || w.status != 0
}

func (w *responseCaptureWriter) WriteHeaderNow() {}

func (w *responseCaptureWriter) Flush() {}

func (w *responseCaptureWriter) Pusher() http.Pusher {
	return w.orig.Pusher()
}

// CatalogHTTPCache stores successful catalog GET responses and serves
// consistent HTTP caching headers/validators (Cache-Control, ETag, Last-Modified).
func CatalogHTTPCache(store *ResponseCacheStore, ttl time.Duration, staleWhileRevalidate time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		if c.Request.Method != http.MethodGet {
			c.Next()
			return
		}

		key := cacheKey(c)

		store.mu.RLock()
		ent, ok := store.data[key]
		store.mu.RUnlock()
		if ok && !time.Now().Before(ent.expires) {
			store.mu.Lock()
			delete(store.data, key)
			store.mu.Unlock()
			ok = false
		}
		if ok && time.Now().Before(ent.expires) {
			setCatalogHeaders(c, ttl, staleWhileRevalidate, ent.eTag, ent.lastMod)
			if isNotModified(c, ent.eTag, ent.lastMod) {
				c.Status(http.StatusNotModified)
				c.Abort()
				return
			}
			if ent.contentType != "" {
				c.Header("Content-Type", ent.contentType)
			}
			c.Status(ent.status)
			_, _ = c.Writer.Write(ent.body)
			c.Abort()
			return
		}

		origWriter := c.Writer
		capture := newResponseCaptureWriter(origWriter)
		c.Writer = capture

		c.Next()

		status := capture.status
		if status == 0 {
			status = http.StatusOK
		}
		if status != http.StatusOK || capture.body.Len() == 0 {
			for hk, vals := range capture.header {
				for _, v := range vals {
					origWriter.Header().Add(hk, v)
				}
			}
			origWriter.WriteHeader(status)
			_, _ = origWriter.Write(capture.body.Bytes())
			c.Writer = origWriter
			return
		}

		lastMod := time.Now().UTC()
		eTag := buildWeakETag(capture.body.Bytes())
		ct := capture.header.Get("Content-Type")
		store.mu.Lock()
		store.cleanupExpiredLocked(lastMod)
		if store.maxEntries > 0 && len(store.data) >= store.maxEntries {
			store.evictOldestLocked(len(store.data) - store.maxEntries + 1)
		}
		store.data[key] = cachedResponse{
			status:      http.StatusOK,
			contentType: ct,
			body:        append([]byte(nil), capture.body.Bytes()...),
			eTag:        eTag,
			lastMod:     lastMod,
			expires:     time.Now().Add(ttl),
		}
		store.mu.Unlock()

		for hk, vals := range capture.header {
			for _, v := range vals {
				origWriter.Header().Add(hk, v)
			}
		}
		maxAge := int(ttl.Seconds())
		if maxAge < 0 {
			maxAge = 0
		}
		stale := int(staleWhileRevalidate.Seconds())
		if stale < 0 {
			stale = 0
		}
		origWriter.Header().Set("Cache-Control", "public, max-age="+strconv.Itoa(maxAge)+", stale-while-revalidate="+strconv.Itoa(stale))
		origWriter.Header().Set("ETag", eTag)
		origWriter.Header().Set("Last-Modified", lastMod.Format(http.TimeFormat))
		if catalogVersion := strings.TrimSpace(os.Getenv("CATALOG_VERSION")); catalogVersion != "" {
			origWriter.Header().Set("X-Catalog-Version", catalogVersion)
		}
		origWriter.WriteHeader(status)
		_, _ = origWriter.Write(capture.body.Bytes())
		c.Writer = origWriter
	}
}

// NoStore marks responses as uncacheable by browsers, intermediaries, and clients.
func NoStore() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Cache-Control", "no-store")
		c.Next()
	}
}

func setCatalogHeaders(c *gin.Context, ttl time.Duration, staleWhileRevalidate time.Duration, eTag string, lastMod time.Time) {
	maxAge := int(ttl.Seconds())
	if maxAge < 0 {
		maxAge = 0
	}
	stale := int(staleWhileRevalidate.Seconds())
	if stale < 0 {
		stale = 0
	}
	c.Header("Cache-Control", "public, max-age="+strconv.Itoa(maxAge)+", stale-while-revalidate="+strconv.Itoa(stale))
	if eTag != "" {
		c.Header("ETag", eTag)
	}
	if !lastMod.IsZero() {
		c.Header("Last-Modified", lastMod.Format(http.TimeFormat))
	}
	if catalogVersion := strings.TrimSpace(os.Getenv("CATALOG_VERSION")); catalogVersion != "" {
		c.Header("X-Catalog-Version", catalogVersion)
	}
}

func buildWeakETag(body []byte) string {
	sum := sha256.Sum256(body)
	return `W/"` + hex.EncodeToString(sum[:]) + `"`
}

func isNotModified(c *gin.Context, eTag string, lastMod time.Time) bool {
	ifNoneMatch := strings.TrimSpace(c.GetHeader("If-None-Match"))
	if ifNoneMatch != "" && eTag != "" {
		// RFC allows comma-separated list; wildcard is also accepted.
		if ifNoneMatch == "*" || matchETagList(ifNoneMatch, eTag) {
			return true
		}
	}

	ifModifiedSince := strings.TrimSpace(c.GetHeader("If-Modified-Since"))
	if ifModifiedSince != "" && !lastMod.IsZero() {
		if t, err := time.Parse(http.TimeFormat, ifModifiedSince); err == nil {
			// HTTP date is second-granularity.
			if !lastMod.After(t.Add(time.Second - time.Nanosecond)) {
				return true
			}
		}
	}
	return false
}

func matchETagList(headerValue string, eTag string) bool {
	parts := strings.Split(headerValue, ",")
	for _, p := range parts {
		if strings.TrimSpace(p) == eTag {
			return true
		}
	}
	return false
}

func (s *ResponseCacheStore) cleanupExpiredLocked(now time.Time) {
	for k, v := range s.data {
		if !now.Before(v.expires) {
			delete(s.data, k)
		}
	}
}

func (s *ResponseCacheStore) evictOldestLocked(n int) {
	if n <= 0 || len(s.data) == 0 {
		return
	}
	if n >= len(s.data) {
		for k := range s.data {
			delete(s.data, k)
		}
		return
	}

	type kv struct {
		key     string
		expires time.Time
	}
	all := make([]kv, 0, len(s.data))
	for k, v := range s.data {
		all = append(all, kv{key: k, expires: v.expires})
	}
	sort.Slice(all, func(i, j int) bool {
		return all[i].expires.Before(all[j].expires)
	})
	for i := 0; i < n; i++ {
		delete(s.data, all[i].key)
	}
}
