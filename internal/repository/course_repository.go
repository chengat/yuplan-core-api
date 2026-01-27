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
	GetByCode(ctx context.Context, courseCode string) ([]models.Course, error)
	Search(ctx context.Context, query string, limit, offset int) ([]models.Course, error)
	GetPaginatedCourses(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error)
	GetCoursesCount(ctx context.Context, faculty, courseCodeRange *string) (int, error)
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

func (r *CourseRepository) GetByCode(ctx context.Context, courseCode string) ([]models.Course, error) {
	// Normalize to match regardless of spaces/case.
	normalized := strings.ToLower(strings.ReplaceAll(courseCode, " ", ""))

	rows, err := r.db.Query(
		ctx,
		`SELECT id, name, code, credits, description, faculty, term, created_at, updated_at
		 FROM courses
		 WHERE REPLACE(LOWER(code), ' ', '') = $1
		 ORDER BY term, code`,
		normalized,
	)
	if err != nil {
		return nil, fmt.Errorf("query courses by code: %w", err)
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
		return nil, fmt.Errorf("iterate courses by code: %w", err)
	}

	return courses, nil
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

// GetPaginatedCourses retrieves courses with pagination and optional filtering by faculty and course code range
func (r *CourseRepository) GetPaginatedCourses(ctx context.Context, page, pageSize int, faculty, courseCodeRange *string) ([]models.Course, error) {
	offset := (page - 1) * pageSize
	
	// Build the WHERE clause dynamically
	whereClauses := []string{}
	args := []interface{}{}
	argIndex := 1
	
	if faculty != nil && *faculty != "" {
		whereClauses = append(whereClauses, fmt.Sprintf("faculty = $%d", argIndex))
		args = append(args, *faculty)
		argIndex++
	}
	
	if courseCodeRange != nil && *courseCodeRange != "" {
		// Parse course code range (e.g., "1000s", "2000s", "5000s+")
		rangeStr := *courseCodeRange
		if strings.HasSuffix(rangeStr, "s+") {
			// Handle "5000s+" case
			baseNum := strings.TrimSuffix(rangeStr, "s+")
			whereClauses = append(whereClauses, fmt.Sprintf(
				"CAST(SUBSTRING(code FROM '\\d+') AS INTEGER) >= $%d",
				argIndex,
			))
			args = append(args, baseNum)
		} else if strings.HasSuffix(rangeStr, "s") {
			// Handle "1000s", "2000s", etc.
			baseNum := strings.TrimSuffix(rangeStr, "s")
			whereClauses = append(whereClauses, fmt.Sprintf(
				"CAST(SUBSTRING(code FROM '\\d+') AS INTEGER) >= $%d AND CAST(SUBSTRING(code FROM '\\d+') AS INTEGER) < $%d",
				argIndex, argIndex+1,
			))
			args = append(args, baseNum)
			argIndex++
			// Calculate upper bound (e.g., 1000s -> 1000-1999, 2000s -> 2000-2999)
			// For "1000s", we want range 1000-1999, so upperBound = first digit + "999"
			var upperBound string
			if len(baseNum) >= 4 {
				// Take first digit and pad rest with 9s (e.g., "1000" -> "1999", "2000" -> "2999")
				upperBound = string(baseNum[0]) + strings.Repeat("9", len(baseNum)-1)
			} else {
				upperBound = baseNum + "999"
			}
			args = append(args, upperBound)
		}
		argIndex++
	}
	
	whereClause := ""
	if len(whereClauses) > 0 {
		whereClause = "WHERE " + strings.Join(whereClauses, " AND ")
	}
	
	// Add pagination parameters
	args = append(args, pageSize, offset)
	limitArg := argIndex
	offsetArg := argIndex + 1
	
	query := fmt.Sprintf(
		`SELECT id, name, code, credits, description, faculty, term, created_at, updated_at
		 FROM courses
		 %s
		 ORDER BY code, term
		 LIMIT $%d OFFSET $%d`,
		whereClause, limitArg, offsetArg,
	)
	
	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query paginated courses: %w", err)
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

// GetCoursesCount returns the total count of courses matching the filters
func (r *CourseRepository) GetCoursesCount(ctx context.Context, faculty, courseCodeRange *string) (int, error) {
	// Build the WHERE clause dynamically (same logic as GetPaginatedCourses)
	whereClauses := []string{}
	args := []interface{}{}
	argIndex := 1
	
	if faculty != nil && *faculty != "" {
		whereClauses = append(whereClauses, fmt.Sprintf("faculty = $%d", argIndex))
		args = append(args, *faculty)
		argIndex++
	}
	
	if courseCodeRange != nil && *courseCodeRange != "" {
		rangeStr := *courseCodeRange
		if strings.HasSuffix(rangeStr, "s+") {
			baseNum := strings.TrimSuffix(rangeStr, "s+")
			whereClauses = append(whereClauses, fmt.Sprintf(
				"CAST(SUBSTRING(code FROM '\\d+') AS INTEGER) >= $%d",
				argIndex,
			))
			args = append(args, baseNum)
		} else if strings.HasSuffix(rangeStr, "s") {
			baseNum := strings.TrimSuffix(rangeStr, "s")
			whereClauses = append(whereClauses, fmt.Sprintf(
				"CAST(SUBSTRING(code FROM '\\d+') AS INTEGER) >= $%d AND CAST(SUBSTRING(code FROM '\\d+') AS INTEGER) < $%d",
				argIndex, argIndex+1,
			))
			args = append(args, baseNum)
			argIndex++
			// Calculate upper bound (e.g., 1000s -> 1000-1999, 2000s -> 2000-2999)
			var upperBound string
			if len(baseNum) >= 4 {
				// Take first digit and pad rest with 9s (e.g., "1000" -> "1999", "2000" -> "2999")
				upperBound = string(baseNum[0]) + strings.Repeat("9", len(baseNum)-1)
			} else {
				upperBound = baseNum + "999"
			}
			args = append(args, upperBound)
		}
		argIndex++
	}
	
	whereClause := ""
	if len(whereClauses) > 0 {
		whereClause = "WHERE " + strings.Join(whereClauses, " AND ")
	}
	
	query := fmt.Sprintf(
		`SELECT COUNT(DISTINCT code) FROM courses %s`,
		whereClause,
	)
	
	var count int
	err := r.db.QueryRow(ctx, query, args...).Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("count courses: %w", err)
	}
	
	return count, nil
}
