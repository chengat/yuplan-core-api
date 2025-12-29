package repository

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/pashagolub/pgxmock"
	"github.com/stretchr/testify/assert"
)

func TestGetTutorialsBySectionID(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewTutorialRepository(mock)

	now := time.Now()
	times := `[{"day": "M", "time": "10:30", "duration": "110"}]`

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM tutorials\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "section_id", "catalog_number", "times", "created_at", "updated_at"}).
			AddRow("tutorial-1", "section-1", "TUTR01", &times, now, now).
			AddRow("tutorial-2", "section-1", "TUTR02", &times, now, now))
	tutorials, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.NoError(t, err)
	assert.NotNil(t, tutorials)
	assert.Len(t, tutorials, 2)
	assert.Equal(t, "tutorial-1", tutorials[0].ID)
	assert.Equal(t, "TUTR01", tutorials[0].CatalogNumber)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetTutorialsBySectionID_WhenQueryErrors_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewTutorialRepository(mock)

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM tutorials\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnError(errors.New("db error"))

	tutorials, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.Error(t, err)
	assert.Nil(t, tutorials)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetTutorialsBySectionID_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewTutorialRepository(mock)

	now := time.Now()
	times := `[{"day": "M", "time": "10:30"}]`
	// Using wrong type for section_id to force scan error
	rows := pgxmock.NewRows([]string{"id", "section_id", "catalog_number", "times", "created_at", "updated_at"}).
		AddRow("tutorial-1", 12345, "TUTR01", &times, now, now)

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM tutorials\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnRows(rows)

	tutorials, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.Error(t, err)
	assert.Nil(t, tutorials)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetTutorialsBySectionID_WhenRowsErr_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewTutorialRepository(mock)

	now := time.Now()
	times := `[{"day": "M", "time": "10:30"}]`
	rows := pgxmock.NewRows([]string{"id", "section_id", "catalog_number", "times", "created_at", "updated_at"}).
		AddRow("tutorial-1", "section-1", "TUTR01", &times, now, now).
		AddRow("tutorial-2", "section-1", "TUTR02", &times, now, now).
		RowError(1, errors.New("rows err"))

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM tutorials\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnRows(rows)

	tutorials, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.Error(t, err)
	assert.Nil(t, tutorials)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetTutorialsBySectionID_EmptyResult(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewTutorialRepository(mock)

	mock.ExpectQuery("SELECT id, section_id, catalog_number, times, created_at, updated_at FROM tutorials\\s+WHERE section_id = \\$1\\s+ORDER BY catalog_number").
		WithArgs("section-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "section_id", "catalog_number", "times", "created_at", "updated_at"}))

	tutorials, err := repo.GetBySectionID(context.Background(), "section-1")
	assert.NoError(t, err)
	assert.NotNil(t, tutorials)
	assert.Len(t, tutorials, 0)
	assert.NoError(t, mock.ExpectationsWereMet())
}
