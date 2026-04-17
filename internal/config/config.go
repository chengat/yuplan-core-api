package config

import (
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	DatabaseURL string
	Port        string

	// POST /api/v1/admin/seed/pipeline (Bearer SEED_PIPELINE_TOKEN)
	SeedPipelineToken    string
	SeedPipelineRepoRoot string
	SeedPipelinePython   string
	SeedPipelineApplyDB  bool
	SeedPipelineTimeout  time.Duration
}

func Load() *Config {
	return &Config{
		DatabaseURL: getEnv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/yuplan?sslmode=disable"),
		Port:        getEnv("PORT", "8080"),

		SeedPipelineToken:    strings.TrimSpace(getEnv("SEED_PIPELINE_TOKEN", "")),
		SeedPipelineRepoRoot: getEnv("YUPLAN_REPO_ROOT", "."),
		SeedPipelinePython:   getEnv("SEED_PIPELINE_PYTHON", "python3"),
		SeedPipelineApplyDB:  getEnvBool("SEED_PIPELINE_APPLY_DB", false),
		SeedPipelineTimeout:  getEnvDurationMinutes("SEED_PIPELINE_TIMEOUT_MINUTES", 45),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvBool(key string, defaultVal bool) bool {
	s := strings.TrimSpace(strings.ToLower(os.Getenv(key)))
	if s == "" {
		return defaultVal
	}
	return s == "1" || s == "true" || s == "yes" || s == "on"
}

func getEnvDurationMinutes(key string, defaultMins int) time.Duration {
	s := strings.TrimSpace(os.Getenv(key))
	if s == "" {
		return time.Duration(defaultMins) * time.Minute
	}
	n, err := strconv.Atoi(s)
	if err != nil || n <= 0 {
		return time.Duration(defaultMins) * time.Minute
	}
	return time.Duration(n) * time.Minute
}
