package repository

import (
	"context"
	"fmt"
	"yuplan/internal/models"

	"github.com/jackc/pgx/v4"
)

type SectionRepositoryInterface interface {
	GetByCourseID(ctx context.Context, courseID string) ([]models.Section, error)
}

type sectionDB interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

type SectionRepository struct {
	db sectionDB
}

func NewSectionRepository(db sectionDB) *SectionRepository {
	return &SectionRepository{db: db}
}

func (r *SectionRepository) GetByCourseID(ctx context.Context, courseID string) ([]models.Section, error) {
	rows, err := r.db.Query(
		ctx,
		`SELECT id, course_id, letter, created_at, updated_at
		 FROM sections
		 WHERE course_id = $1
		 ORDER BY letter`,
		courseID,
	)
	if err != nil {
		return nil, fmt.Errorf("query sections by course_id: %w", err)
	}
	defer rows.Close()

	sections := make([]models.Section, 0)
	for rows.Next() {
		var sec models.Section
		if err := rows.Scan(&sec.ID, &sec.CourseID, &sec.Letter, &sec.CreatedAt, &sec.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan section: %w", err)
		}
		sections = append(sections, sec)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate sections: %w", err)
	}

	return sections, nil
}

