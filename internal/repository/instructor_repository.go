package repository

import (
	"context"
	"fmt"
	"yuplan/internal/models"

	"github.com/jackc/pgx/v4"
)

type InstructorRepositoryInterface interface {
	GetByCourseID(ctx context.Context, courseID string) ([]models.Instructor, error)
}

type instructorDB interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

type InstructorRepository struct {
	db instructorDB
}

func NewInstructorRepository(db instructorDB) *InstructorRepository {
	return &InstructorRepository{db: db}
}

func (r *InstructorRepository) GetByCourseID(ctx context.Context, courseID string) ([]models.Instructor, error) {
	rows, err := r.db.Query(
		ctx,
		`SELECT i.id, i.first_name, i.last_name, i.rate_my_prof_link, i.section_id, i.created_at, i.updated_at
		 FROM instructors i
		 INNER JOIN sections s ON i.section_id = s.id
		 WHERE s.course_id = $1
		 ORDER BY s.letter, i.last_name, i.first_name`,
		courseID,
	)
	if err != nil {
		return nil, fmt.Errorf("query instructors by course_id: %w", err)
	}
	defer rows.Close()

	instructors := make([]models.Instructor, 0)
	for rows.Next() {
		var inst models.Instructor
		if err := rows.Scan(&inst.ID, &inst.FirstName, &inst.LastName, &inst.RateMyProfLink, &inst.SectionID, &inst.CreatedAt, &inst.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan instructor: %w", err)
		}
		instructors = append(instructors, inst)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate instructors: %w", err)
	}

	return instructors, nil
}

