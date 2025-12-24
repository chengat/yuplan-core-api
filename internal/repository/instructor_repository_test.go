package repository

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/pashagolub/pgxmock"
	"github.com/stretchr/testify/assert"
)

func TestGetInstructorsByCourseID(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewInstructorRepository(mock)

	now := time.Now()
	rmpLink1 := "https://www.ratemyprofessors.com/search/professors/?q=John+Doe"
	rmpLink2 := "https://www.ratemyprofessors.com/search/professors/?q=Jane+Smith"
	sectionID1 := "section-1"
	sectionID2 := "section-2"
	
	mock.ExpectQuery("SELECT i.id, i.first_name, i.last_name, i.rate_my_prof_link, i.section_id, i.created_at, i.updated_at FROM instructors i\\s+INNER JOIN sections s ON i.section_id = s.id\\s+WHERE s.course_id = \\$1\\s+ORDER BY s.letter, i.last_name, i.first_name").
		WithArgs("course-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "first_name", "last_name", "rate_my_prof_link", "section_id", "created_at", "updated_at"}).
			AddRow("instructor-1", "John", "Doe", &rmpLink1, &sectionID1, now, now).
			AddRow("instructor-2", "Jane", "Smith", &rmpLink2, &sectionID2, now, now))

	instructors, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.NoError(t, err)
	assert.NotNil(t, instructors)
	assert.Len(t, instructors, 2)
	assert.Equal(t, "instructor-1", instructors[0].ID)
	assert.Equal(t, "John", instructors[0].FirstName)
	assert.Equal(t, "Doe", instructors[0].LastName)
	assert.Equal(t, "instructor-2", instructors[1].ID)
	assert.Equal(t, "Jane", instructors[1].FirstName)
	assert.Equal(t, "Smith", instructors[1].LastName)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetInstructorsByCourseID_WhenQueryErrors_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewInstructorRepository(mock)

	mock.ExpectQuery("SELECT i.id, i.first_name, i.last_name, i.rate_my_prof_link, i.section_id, i.created_at, i.updated_at FROM instructors i\\s+INNER JOIN sections s ON i.section_id = s.id\\s+WHERE s.course_id = \\$1\\s+ORDER BY s.letter, i.last_name, i.first_name").
		WithArgs("course-1").
		WillReturnError(errors.New("db error"))

	instructors, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, instructors)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetInstructorsByCourseID_WhenScanFails_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewInstructorRepository(mock)

	now := time.Now()
	rmpLink := "https://www.ratemyprofessors.com/search/professors/?q=John+Doe"
	sectionID := "section-1"
	// Using wrong type for id to force scan error
	rows := pgxmock.NewRows([]string{"id", "first_name", "last_name", "rate_my_prof_link", "section_id", "created_at", "updated_at"}).
		AddRow(12345, "John", "Doe", &rmpLink, &sectionID, now, now)

	mock.ExpectQuery("SELECT i.id, i.first_name, i.last_name, i.rate_my_prof_link, i.section_id, i.created_at, i.updated_at FROM instructors i\\s+INNER JOIN sections s ON i.section_id = s.id\\s+WHERE s.course_id = \\$1\\s+ORDER BY s.letter, i.last_name, i.first_name").
		WithArgs("course-1").
		WillReturnRows(rows)

	instructors, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, instructors)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetInstructorsByCourseID_WhenRowsErr_ReturnsError(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewInstructorRepository(mock)

	now := time.Now()
	rmpLink := "https://www.ratemyprofessors.com/search/professors/?q=John+Doe"
	sectionID := "section-1"
	rows := pgxmock.NewRows([]string{"id", "first_name", "last_name", "rate_my_prof_link", "section_id", "created_at", "updated_at"}).
		AddRow("instructor-1", "John", "Doe", &rmpLink, &sectionID, now, now).
		AddRow("instructor-2", "Jane", "Smith", &rmpLink, &sectionID, now, now).
		RowError(1, errors.New("rows err"))

	mock.ExpectQuery("SELECT i.id, i.first_name, i.last_name, i.rate_my_prof_link, i.section_id, i.created_at, i.updated_at FROM instructors i\\s+INNER JOIN sections s ON i.section_id = s.id\\s+WHERE s.course_id = \\$1\\s+ORDER BY s.letter, i.last_name, i.first_name").
		WithArgs("course-1").
		WillReturnRows(rows)

	instructors, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.Error(t, err)
	assert.Nil(t, instructors)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetInstructorsByCourseID_EmptyResult(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewInstructorRepository(mock)

	mock.ExpectQuery("SELECT i.id, i.first_name, i.last_name, i.rate_my_prof_link, i.section_id, i.created_at, i.updated_at FROM instructors i\\s+INNER JOIN sections s ON i.section_id = s.id\\s+WHERE s.course_id = \\$1\\s+ORDER BY s.letter, i.last_name, i.first_name").
		WithArgs("course-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "first_name", "last_name", "rate_my_prof_link", "section_id", "created_at", "updated_at"}))

	instructors, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.NoError(t, err)
	assert.NotNil(t, instructors)
	assert.Len(t, instructors, 0)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestGetInstructorsByCourseID_WithNilFields(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewInstructorRepository(mock)

	now := time.Now()
	
	mock.ExpectQuery("SELECT i.id, i.first_name, i.last_name, i.rate_my_prof_link, i.section_id, i.created_at, i.updated_at FROM instructors i\\s+INNER JOIN sections s ON i.section_id = s.id\\s+WHERE s.course_id = \\$1\\s+ORDER BY s.letter, i.last_name, i.first_name").
		WithArgs("course-1").
		WillReturnRows(pgxmock.NewRows([]string{"id", "first_name", "last_name", "rate_my_prof_link", "section_id", "created_at", "updated_at"}).
			AddRow("instructor-1", "John", "Doe", nil, nil, now, now))

	instructors, err := repo.GetByCourseID(context.Background(), "course-1")
	assert.NoError(t, err)
	assert.NotNil(t, instructors)
	assert.Len(t, instructors, 1)
	assert.Nil(t, instructors[0].RateMyProfLink)
	assert.Nil(t, instructors[0].SectionID)
	assert.NoError(t, mock.ExpectationsWereMet())
}

