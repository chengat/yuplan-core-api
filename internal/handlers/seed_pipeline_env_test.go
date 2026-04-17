package handlers

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestEnvWithSISCookie_OverridesExisting(t *testing.T) {
	base := []string{"PATH=/bin", "YORK_SIS_COOKIE=old", "HOME=/tmp"}
	out := envWithSISCookie(base, "a=b; c=d")

	assert.Equal(t, []string{"PATH=/bin", "HOME=/tmp", "YORK_SIS_COOKIE=a=b; c=d"}, out)
}

func TestEnvWithSISCookie_EmptyLeavesBase(t *testing.T) {
	base := []string{"PATH=/bin", "YORK_SIS_COOKIE=keep"}
	assert.Equal(t, base, envWithSISCookie(base, ""))
}
