package config

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestLoadConfig(t *testing.T) {
	os.Setenv("DATABASE_URL", "test_database_url")
	os.Setenv("PORT", "9090")

	config := Load()

	assert.Equal(t, "test_database_url", config.DatabaseURL)
	assert.Equal(t, "9090", config.Port)
}
