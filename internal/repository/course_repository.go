package repository

import (
	"context"
	"fmt"
	"yuplan/internal/models"

	"github.com/jackc/pgx/v5/pgxpool"
)

type CourseRepository struct {
	db *pgxpool.Pool
}

func NewCourseRepository(db *pgxpool.Pool) *CourseRepository {
	return &CourseRepository{db: db}
}

func (r *CourseRepository) GetAll(ctx context.Context, limit, offset int) ([]models.Course, error) {
	query := `
        SELECT id, name, code, credits, description, created_at, updated_at
        FROM courses
        ORDER BY code
        LIMIT $1 OFFSET $2
    `

	rows, err := r.db.Query(ctx, query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query courses: %w", err)
	}
	defer rows.Close()

	var courses []models.Course
	for rows.Next() {
		var course models.Course
		err := rows.Scan(
			&course.ID,
			&course.Name,
			&course.Code,
			&course.Credits,
			&course.Description,
			&course.CreatedAt,
			&course.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan course: %w", err)
		}
		courses = append(courses, course)
	}

	return courses, rows.Err()
}

func (r *CourseRepository) GetByID(ctx context.Context, courseID string) (*models.Course, error) {
	// Get course
	courseQuery := `
        SELECT id, name, code, credits, description, created_at, updated_at
        FROM courses
        WHERE id = $1
    `

	var course models.Course
	err := r.db.QueryRow(ctx, courseQuery, courseID).Scan(
		&course.ID,
		&course.Name,
		&course.Code,
		&course.Credits,
		&course.Description,
		&course.CreatedAt,
		&course.UpdatedAt,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to get course: %w", err)
	}

	return &course, nil
}
