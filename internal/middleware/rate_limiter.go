package middleware

import (
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

type visitor struct {
	requests  int
	lastReset time.Time
}

type RateLimiter struct {
	visitors map[string]*visitor
	mu       sync.RWMutex
	limit    int           // requests per window
	window   time.Duration // time window
	cleanup  time.Duration // cleanup interval
}

// NewRateLimiter creates a new rate limiter
// limit: max requests per window (e.g., 100)
// window: time window (e.g., 1 minute)
func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
	rl := &RateLimiter{
		visitors: make(map[string]*visitor),
		limit:    limit,
		window:   window,
		cleanup:  window * 2,
	}
	
	// Start cleanup goroutine to prevent memory leaks
	go rl.cleanupVisitors()
	
	return rl
}

func (rl *RateLimiter) cleanupVisitors() {
	ticker := time.NewTicker(rl.cleanup)
	defer ticker.Stop()
	
	for range ticker.C {
		rl.mu.Lock()
		now := time.Now()
		for ip, v := range rl.visitors {
			if now.Sub(v.lastReset) > rl.cleanup {
				delete(rl.visitors, ip)
			}
		}
		rl.mu.Unlock()
	}
}

func (rl *RateLimiter) getVisitor(ip string) *visitor {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	
	v, exists := rl.visitors[ip]
	if !exists {
		v = &visitor{
			requests:  0,
			lastReset: time.Now(),
		}
		rl.visitors[ip] = v
	}
	
	return v
}

func (rl *RateLimiter) Limit() gin.HandlerFunc {
	return func(c *gin.Context) {
		ip := c.ClientIP()
		
		rl.mu.Lock()
		v := rl.visitors[ip]
		if v == nil {
			v = &visitor{
				requests:  0,
				lastReset: time.Now(),
			}
			rl.visitors[ip] = v
		}
		
		now := time.Now()
		
		// Reset counter if window has passed
		if now.Sub(v.lastReset) > rl.window {
			v.requests = 0
			v.lastReset = now
		}
		
		// Check if limit exceeded
		if v.requests >= rl.limit {
			rl.mu.Unlock()
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error": "Rate limit exceeded. Please try again later.",
			})
			c.Abort()
			return
		}
		
		// Increment counter
		v.requests++
		rl.mu.Unlock()
		
		c.Next()
	}
}
