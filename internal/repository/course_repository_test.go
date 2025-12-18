package repository

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/pashagolub/pgxmock"
	"github.com/stretchr/testify/assert"
)

func TestGetAllCourses(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	mock.ExpectQuery("SELECT id, name, code, credits, description, created_at, updated_at FROM courses\\s+LIMIT \\$1 OFFSET \\$2").
		WithArgs(10, 0).
		WillReturnRows(pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "created_at", "updated_at"}))

	courses, err := repo.GetAll(context.Background(), 10, 0)
	assert.NoError(t, err)
	assert.NotNil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetCourseByID(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	mock.ExpectQuery("SELECT id, name, code, credits, description, created_at, updated_at FROM courses\\s+WHERE id = \\$1").
		WithArgs("test-id").
		WillReturnRows(pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "created_at", "updated_at"}).
			AddRow("test-id", "Test Course", "TC101", 3.0, &desc, now, now))

	course, err := repo.GetByID(context.Background(), "test-id")
	assert.NoError(t, err)
	assert.NotNil(t, course)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetAllCourses_WhenQueryErrors_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	mock.ExpectQuery("SELECT id, name, code, credits, description, created_at, updated_at FROM courses\\s+LIMIT \\$1 OFFSET \\$2").
		WithArgs(10, 0).
		WillReturnError(errors.New("boom"))

	courses, err := repo.GetAll(context.Background(), 10, 0)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetAllCourses_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	// credits is intentionally the wrong type to force the scan to fail (expects float64).
	rows := pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "created_at", "updated_at"}).
		AddRow("test-id", "Test Course", "TC101", "NOT_A_FLOAT", &desc, now, now)

	mock.ExpectQuery("SELECT id, name, code, credits, description, created_at, updated_at FROM courses\\s+LIMIT \\$1 OFFSET \\$2").
		WithArgs(10, 0).
		WillReturnRows(rows)

	courses, err := repo.GetAll(context.Background(), 10, 0)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetAllCourses_WhenRowsErr_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	// Trigger rows.Err() by injecting an error on the second row iteration.
	rows := pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "created_at", "updated_at"}).
		AddRow("id-1", "Course 1", "C1", 3.0, &desc, now, now).
		AddRow("id-2", "Course 2", "C2", 3.0, &desc, now, now).
		RowError(1, errors.New("rows err"))

	mock.ExpectQuery("SELECT id, name, code, credits, description, created_at, updated_at FROM courses\\s+LIMIT \\$1 OFFSET \\$2").
		WithArgs(10, 0).
		WillReturnRows(rows)

	courses, err := repo.GetAll(context.Background(), 10, 0)
	assert.Error(t, err)
	assert.Nil(t, courses)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetCourseByID_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewCourseRepository(mock)

	now := time.Now()
	desc := "Description"
	// credits wrong type forces a scan error.
	rows := pgxmock.NewRows([]string{"id", "name", "code", "credits", "description", "created_at", "updated_at"}).
		AddRow("test-id", "Test Course", "TC101", "NOT_A_FLOAT", &desc, now, now)

	mock.ExpectQuery("SELECT id, name, code, credits, description, created_at, updated_at FROM courses\\s+WHERE id = \\$1").
		WithArgs("test-id").
		WillReturnRows(rows)

	course, err := repo.GetByID(context.Background(), "test-id")
	assert.Error(t, err)
	assert.Nil(t, course)
	assert.NoError(t, mock.ExpectationsWereMet())
}
