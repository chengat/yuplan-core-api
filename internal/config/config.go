package config

import (
	"os"
	"strings"
)

type Config struct {
	DatabaseURL string
	Port        string

	// POST /api/v1/admin/seed/pipeline — Bearer shared secret (you choose the value).
	// Everything else for that route is hardcoded (python3, 45m timeout, cwd = repo root at startup).
	// If DATABASE_URL is set, the pipeline also runs scripts/seed.sh after generating db/seed.sql.
	SeedPipelineToken string
}

func Load() *Config {
	return &Config{
		DatabaseURL: getEnv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/yuplan?sslmode=disable"),
		Port:        getEnv("PORT", "8080"),

		SeedPipelineToken: strings.TrimSpace(getEnv("SEED_PIPELINE_TOKEN", "")),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
