package repository

import (
	"context"
	"fmt"
	"yuplan/internal/models"

	"github.com/jackc/pgx/v4"
)

type TutorialRepositoryInterface interface {
	GetBySectionID(ctx context.Context, sectionID string) ([]models.Tutorial, error)
}

type tutorialDB interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

type TutorialRepository struct {
	db tutorialDB
}

func NewTutorialRepository(db tutorialDB) *TutorialRepository {
	return &TutorialRepository{db: db}
}

func (r *TutorialRepository) GetBySectionID(ctx context.Context, sectionID string) ([]models.Tutorial, error) {
	rows, err := r.db.Query(
		ctx,
		`SELECT id, section_id, catalog_number, times, created_at, updated_at
		 FROM tutorials
		 WHERE section_id = $1
		 ORDER BY catalog_number`,
		sectionID,
	)
	if err != nil {
		return nil, fmt.Errorf("query tutorials by section_id: %w", err)
	}
	defer rows.Close()

	tutorials := make([]models.Tutorial, 0)
	for rows.Next() {
		var tutorial models.Tutorial
		if err := rows.Scan(&tutorial.ID, &tutorial.SectionID, &tutorial.CatalogNumber, &tutorial.Times, &tutorial.CreatedAt, &tutorial.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan tutorial: %w", err)
		}
		tutorials = append(tutorials, tutorial)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate tutorials: %w", err)
	}

	return tutorials, nil
}

