package repository

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/pashagolub/pgxmock"
	"github.com/stretchr/testify/assert"
)

func TestGetSectionsByCourseID(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewSectionRepository(mock)

	now := time.Now()

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "course_id", "letter", "created_at", "updated_at"}).
			AddRow("section-1", "course-1", "A", now, now).
			AddRow("section-2", "course-1", "B", now, now))

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.NoError(t, err)
	assert.NotNil(t, sections)
	assert.Len(t, sections, 2)
	assert.Equal(t, "section-1", sections[0].ID)
	assert.Equal(t, "course-1", sections[0].CourseID)
	assert.Equal(t, "A", sections[0].Letter)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetSectionsByCourseID_WhenQueryErrors_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewSectionRepository(mock)

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnError(errors.New("db error"))

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, sections)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetSectionsByCourseID_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewSectionRepository(mock)

	now := time.Now()
	// Wrong type for course_id to force scan error
	rows := pgxmock.NewRows([]string{"id", "course_id", "letter", "created_at", "updated_at"}).
		AddRow("section-1", 12345, "A", now, now)

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnRows(rows)

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, sections)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetSectionsByCourseID_WhenRowsErr_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewSectionRepository(mock)

	now := time.Now()
	rows := pgxmock.NewRows([]string{"id", "course_id", "letter", "created_at", "updated_at"}).
		AddRow("section-1", "course-1", "A", now, now).
		AddRow("section-2", "course-1", "B", now, now).
		RowError(1, errors.New("rows err"))

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnRows(rows)

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, sections)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetSectionsByCourseID_EmptyResult(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewSectionRepository(mock)

	mock.ExpectQuery("SELECT id, course_id, letter, created_at, updated_at FROM sections\\s+WHERE course_id = \\$1\\s+ORDER BY letter").
		WithArgs("course-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "course_id", "letter", "created_at", "updated_at"}))

	sections, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.NoError(t, err)
	assert.NotNil(t, sections)
	assert.Len(t, sections, 0)
	assert.NoError(t, mock.ExpectationsWereMet())
}

