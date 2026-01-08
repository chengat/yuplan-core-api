package repository

import (
	"context"
	"fmt"
	"strings"
	"yuplan/internal/models"

	"github.com/jackc/pgx/v4"
)

type CourseRepositoryInterface interface {
	GetRandomCourses(ctx context.Context, limit int) ([]models.Course, error)
	GetByID(ctx context.Context, courseID string) (*models.Course, error)
	Search(ctx context.Context, query string, limit, offset int) ([]models.Course, error)
}

type courseDB interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
	QueryRow(ctx context.Context, sql string, args ...any) pgx.Row
}

type CourseRepository struct {
	db courseDB
}

func NewCourseRepository(db courseDB) *CourseRepository {
	return &CourseRepository{db: db}
}

func (r *CourseRepository) GetRandomCourses(ctx context.Context, limit int) ([]models.Course, error) {
	rows, err := r.db.Query(
		ctx,
		`SELECT id, name, code, credits, description, faculty, term, created_at, updated_at
		 FROM courses TABLESAMPLE SYSTEM (10)
		 ORDER BY RANDOM()
		 LIMIT $1`,
		limit,
	)
	if err != nil {
		return nil, fmt.Errorf("query courses: %w", err)
	}
	defer rows.Close()

	courses := make([]models.Course, 0)
	for rows.Next() {
		var c models.Course
		if err := rows.Scan(&c.ID, &c.Name, &c.Code, &c.Credits, &c.Description, &c.Faculty, &c.Term, &c.CreatedAt, &c.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan course: %w", err)
		}
		courses = append(courses, c)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate courses: %w", err)
	}

	return courses, nil
}

func (r *CourseRepository) GetByID(ctx context.Context, courseID string) (*models.Course, error) {
	row := r.db.QueryRow(
		ctx,
		`SELECT id, name, code, credits, description, faculty, term, created_at, updated_at
		 FROM courses
		 WHERE id = $1`,
		courseID,
	)

	var course models.Course
	if err := row.Scan(&course.ID, &course.Name, &course.Code, &course.Credits, &course.Description, &course.Faculty, &course.Term, &course.CreatedAt, &course.UpdatedAt); err != nil {
		return nil, fmt.Errorf("scan course by id: %w", err)
	}
	return &course, nil
}

func (r *CourseRepository) Search(ctx context.Context, query string, limit, offset int) ([]models.Course, error) {
	searchPattern := "%" + query + "%"
	normalizedPattern := "%" + strings.ReplaceAll(query, " ", "") + "%"
	rows, err := r.db.Query(
		ctx,
		`SELECT id, name, code, credits, description, faculty, term, created_at, updated_at
		 FROM courses
		 WHERE name ILIKE $1 OR code ILIKE $1 OR REPLACE(code, ' ', '') ILIKE $2
		 ORDER BY code
		 LIMIT $3 OFFSET $4`,
		searchPattern, normalizedPattern, limit, offset,
	)
	if err != nil {
		return nil, fmt.Errorf("search courses: %w", err)
	}
	defer rows.Close()

	courses := make([]models.Course, 0)
	for rows.Next() {
		var c models.Course
		if err := rows.Scan(&c.ID, &c.Name, &c.Code, &c.Credits, &c.Description, &c.Faculty, &c.Term, &c.CreatedAt, &c.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan course: %w", err)
		}
		courses = append(courses, c)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate courses: %w", err)
	}

	return courses, nil
}
