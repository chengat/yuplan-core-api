package database

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewPool(t *testing.T) {
	t.Run("invalid database url returns parse error", func(t *testing.T) {
		// pgxpool.ParseConfig fails before any network/database work is attempted,
		// so this is safe to run in unit tests.
		pool, err := NewPool(context.Background(), "://not-a-valid-url")
		assert.Error(t, err)
		assert.Nil(t, pool)
	})
}
