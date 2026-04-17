package handlers

import (
	"bytes"
	"context"
	"crypto/subtle"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	seedPipelinePython  = "python3"
	seedPipelineTimeout = 45 * time.Minute
)

// SeedPipelineHandler runs scripts/run_seed_pipeline.py (fetch → scrape → db/seed.sql).
// If databaseURL is non-empty, also passes --apply-db so scripts/seed.sh runs (uses DATABASE_URL from the child env).
type SeedPipelineHandler struct {
	mu       sync.Mutex
	token    string
	repoRoot string
	applyDB  bool
}

// NewSeedPipelineHandler configures the admin seed route. Repo root is usually os.Getwd() at startup (deploy from repo root).
// applyDB is true when databaseURL is non-empty so the child process runs scripts/seed.sh (inherits DATABASE_URL).
func NewSeedPipelineHandler(token, databaseURL, repoRoot string) *SeedPipelineHandler {
	if repoRoot == "" {
		repoRoot = "."
	}
	return &SeedPipelineHandler{
		token:    strings.TrimSpace(token),
		repoRoot: repoRoot,
		applyDB:  strings.TrimSpace(databaseURL) != "",
	}
}

// Post triggers the pipeline asynchronously.
// Optional JSON body: {"cookie":"…"} — forwarded as YORK_SIS_COOKIE for this run (overrides server env when non-empty).
// Auth: Authorization: Bearer <SEED_PIPELINE_TOKEN>.
func (h *SeedPipelineHandler) Post(c *gin.Context) {
	if h.token == "" {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "seed pipeline not configured (set SEED_PIPELINE_TOKEN)"})
		return
	}

	raw := strings.TrimSpace(c.GetHeader("Authorization"))
	if !strings.HasPrefix(strings.ToLower(raw), "bearer ") {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "missing bearer token"})
		return
	}
	got := strings.TrimSpace(raw[7:])
	if subtle.ConstantTimeCompare([]byte(got), []byte(h.token)) != 1 {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	sisCookie, ok := readOptionalSISCookieBody(c)
	if !ok {
		return
	}

	if !h.mu.TryLock() {
		c.JSON(http.StatusConflict, gin.H{"error": "seed pipeline already running"})
		return
	}

	go h.runLocked(sisCookie)

	c.JSON(http.StatusAccepted, gin.H{"status": "accepted", "apply_db": h.applyDB})
}

func readOptionalSISCookieBody(c *gin.Context) (string, bool) {
	body, err := io.ReadAll(c.Request.Body)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "could not read body"})
		return "", false
	}
	trim := bytes.TrimSpace(body)
	if len(trim) == 0 {
		return "", true
	}

	var req struct {
		Cookie string `json:"cookie"`
	}
	if err := json.Unmarshal(trim, &req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": `invalid json; use {} or {"cookie":"…"}`})
		return "", false
	}
	return strings.TrimSpace(req.Cookie), true
}

// envWithSISCookie returns base env with YORK_SIS_COOKIE set to sisCookie when non-empty (replacing any existing value).
func envWithSISCookie(base []string, sisCookie string) []string {
	if sisCookie == "" {
		return base
	}
	out := make([]string, 0, len(base)+1)
	for _, kv := range base {
		if strings.HasPrefix(kv, "YORK_SIS_COOKIE=") {
			continue
		}
		out = append(out, kv)
	}
	return append(out, "YORK_SIS_COOKIE="+sisCookie)
}

func (h *SeedPipelineHandler) runLocked(sisCookie string) {
	defer h.mu.Unlock()

	ctx, cancel := context.WithTimeout(context.Background(), seedPipelineTimeout)
	defer cancel()

	script := filepath.Join(h.repoRoot, "scripts", "run_seed_pipeline.py")
	args := []string{script}
	if h.applyDB {
		args = append(args, "--apply-db")
	}

	cmd := exec.CommandContext(ctx, seedPipelinePython, args...)
	cmd.Dir = h.repoRoot
	cmd.Env = envWithSISCookie(os.Environ(), sisCookie)

	var buf bytes.Buffer
	cmd.Stdout = &buf
	cmd.Stderr = &buf

	if err := cmd.Run(); err != nil {
		log.Printf("seed pipeline failed: %v\n%s", err, buf.String())
		return
	}
	log.Printf("seed pipeline finished:\n%s", buf.String())
}
