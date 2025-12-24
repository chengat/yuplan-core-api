package repository

import (
	"context"
	"fmt"
	"yuplan/internal/models"

	"github.com/jackc/pgx/v4"
)

type LabRepositoryInterface interface {
	GetBySectionID(ctx context.Context, sectionID string) ([]models.Lab, error)
}

type labDB interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

type LabRepository struct {
	db labDB
}

func NewLabRepository(db labDB) *LabRepository {
	return &LabRepository{db: db}
}

func (r *LabRepository) GetBySectionID(ctx context.Context, sectionID string) ([]models.Lab, error) {
	rows, err := r.db.Query(
		ctx,
		`SELECT id, section_id, catalog_number, times, created_at, updated_at
		 FROM labs
		 WHERE section_id = $1
		 ORDER BY catalog_number`,
		sectionID,
	)
	if err != nil {
		return nil, fmt.Errorf("query labs by section_id: %w", err)
	}
	defer rows.Close()

	labs := make([]models.Lab, 0)
	for rows.Next() {
		var lab models.Lab
		if err := rows.Scan(&lab.ID, &lab.SectionID, &lab.CatalogNumber, &lab.Times, &lab.CreatedAt, &lab.UpdatedAt); err != nil {
			return nil, fmt.Errorf("scan lab: %w", err)
		}
		labs = append(labs, lab)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate labs: %w", err)
	}

	return labs, nil
}

