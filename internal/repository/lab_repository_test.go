package repository

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/pashagolub/pgxmock"
	"github.com/stretchr/testify/assert"
)

func TestGetLabsBySectionID(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewLabRepository(mock)

	now := time.Now()
	times := `[{"day": "M", "time": "10:30", "duration": "110"}]`

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM labs\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "section_id", "catalog_number", "times", "created_at", "updated_at"}).
			AddRow("lab-1", "section-1", "LAB001", &times, now, now).
			AddRow("lab-2", "section-1", "LAB002", &times, now, now))

	labs, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.NoError(t, err)
	assert.NotNil(t, labs)
	assert.Len(t, labs, 2)
	assert.Equal(t, "lab-1", labs[0].ID)
	assert.Equal(t, "LAB001", labs[0].CatalogNumber)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetLabsBySectionID_WhenQueryErrors_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewLabRepository(mock)

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM labs\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnError(errors.New("db error"))

	labs, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.Error(t, err)
	assert.Nil(t, labs)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetLabsBySectionID_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewLabRepository(mock)

	now := time.Now()
	times := `[{"day": "M", "time": "10:30"}]`
	// Using wrong type for section_id to force scan error
	rows := pgxmock.NewRows([]string{"id", "section_id", "catalog_number", "times", "created_at", "updated_at"}).
		AddRow("lab-1", 12345, "LAB001", &times, now, now)

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM labs\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnRows(rows)

	labs, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.Error(t, err)
	assert.Nil(t, labs)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetLabsBySectionID_WhenRowsErr_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewLabRepository(mock)

	now := time.Now()
	times := `[{"day": "M", "time": "10:30"}]`
	rows := pgxmock.NewRows([]string{"id", "section_id", "catalog_number", "times", "created_at", "updated_at"}).
		AddRow("lab-1", "section-1", "LAB001", &times, now, now).
		AddRow("lab-2", "section-1", "LAB002", &times, now, now).
		RowError(1, errors.New("rows err"))

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM labs\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnRows(rows)

	labs, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.Error(t, err)
	assert.Nil(t, labs)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetLabsBySectionID_EmptyResult(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewLabRepository(mock)

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM labs\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "section_id", "catalog_number", "times", "created_at", "updated_at"}))

	labs, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.NoError(t, err)
	assert.NotNil(t, labs)
	assert.Len(t, labs, 0)
	assert.NoError(t, mock.ExpectationsWereMet())
}
