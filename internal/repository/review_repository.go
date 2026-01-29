package repository

import (
	"context"
	"fmt"
	"time"
	"yuplan/internal/models"

	"github.com/jackc/pgconn"
	"github.com/jackc/pgx/v4"
)

type ReviewRepositoryInterface interface {
	Create(ctx context.Context, review *models.Review) error
	GetByCourseCode(ctx context.Context, courseCode string, sortBy string, limit, offset int) ([]models.Review, error)
	GetCourseStats(ctx context.Context, courseCode string) (map[string]interface{}, error)
	GetAll(ctx context.Context) ([]models.Review, error)
}

type reviewDB interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
	QueryRow(ctx context.Context, sql string, args ...any) pgx.Row
	Exec(ctx context.Context, sql string, args ...any) (pgconn.CommandTag, error)
}

type ReviewRepository struct {
	db reviewDB
}

func NewReviewRepository(db reviewDB) *ReviewRepository {
	return &ReviewRepository{db: db}
}

func (r *ReviewRepository) Create(ctx context.Context, review *models.Review) error {
	review.CreatedAt = time.Now()
	review.UpdatedAt = time.Now()

	query := `
		INSERT INTO reviews (course_code, email, author_name, liked, difficulty, real_world_relevance, review_text, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		RETURNING id
	`
	err := r.db.QueryRow(ctx, query,
		review.CourseCode,
		review.Email,
		review.AuthorName,
		review.Liked,
		review.Difficulty,
		review.RealWorldRelevance,
		review.ReviewText,
		review.CreatedAt,
		review.UpdatedAt,
	).Scan(&review.ID)
	return err
}

func (r *ReviewRepository) GetByCourseCode(ctx context.Context, courseCode string, sortBy string, limit, offset int) ([]models.Review, error) {
	var orderClause string
	switch sortBy {
	case "earliest":
		orderClause = "ORDER BY created_at ASC"
	case "recent":
		fallthrough
	default:
		orderClause = "ORDER BY created_at DESC"
	}

	query := fmt.Sprintf(`
		SELECT 
			id,
			course_code,
			email,
			author_name,
			liked,
			difficulty,
			real_world_relevance,
			review_text,
			created_at,
			updated_at
		FROM reviews
		WHERE course_code = $1
		%s
		LIMIT $2 OFFSET $3
	`, orderClause)

	rows, err := r.db.Query(ctx, query, courseCode, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var reviews []models.Review
	for rows.Next() {
		var review models.Review
		err := rows.Scan(
			&review.ID,
			&review.CourseCode,
			&review.Email,
			&review.AuthorName,
			&review.Liked,
			&review.Difficulty,
			&review.RealWorldRelevance,
			&review.ReviewText,
			&review.CreatedAt,
			&review.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		reviews = append(reviews, review)
	}

	return reviews, nil
}

func (r *ReviewRepository) GetCourseStats(ctx context.Context, courseCode string) (map[string]interface{}, error) {
	query := `
		SELECT 
			COUNT(*) as total_reviews,
			COALESCE(SUM(CASE WHEN liked = true THEN 1 ELSE 0 END), 0) as likes,
			COALESCE(SUM(CASE WHEN liked = false THEN 1 ELSE 0 END), 0) as dislikes,
			COALESCE(AVG(difficulty), 0) as avg_difficulty,
			COALESCE(AVG(real_world_relevance), 0) as avg_real_world_relevance
		FROM reviews
		WHERE course_code = $1
	`

	var stats struct {
		TotalReviews          int
		Likes                 int
		Dislikes              int
		AvgDifficulty         float64
		AvgRealWorldRelevance float64
	}

	err := r.db.QueryRow(ctx, query, courseCode).Scan(
		&stats.TotalReviews,
		&stats.Likes,
		&stats.Dislikes,
		&stats.AvgDifficulty,
		&stats.AvgRealWorldRelevance,
	)
	if err != nil {
		return nil, err
	}

	likePercentage := 0
	if stats.TotalReviews > 0 {
		likePercentage = int(float64(stats.Likes) / float64(stats.TotalReviews) * 100)
	}

	return map[string]interface{}{
		"total_reviews":            stats.TotalReviews,
		"likes":                    stats.Likes,
		"dislikes":                 stats.Dislikes,
		"like_percentage":          likePercentage,
		"avg_difficulty":           stats.AvgDifficulty,
		"avg_real_world_relevance": stats.AvgRealWorldRelevance,
	}, nil
}

func (r *ReviewRepository) GetAll(ctx context.Context) ([]models.Review, error) {
	query := `
		SELECT 
			id,
			course_code,
			email,
			author_name,
			liked,
			difficulty,
			real_world_relevance,
			review_text,
			created_at,
			updated_at
		FROM reviews
		ORDER BY created_at DESC
	`

	rows, err := r.db.Query(ctx, query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var reviews []models.Review
	for rows.Next() {
		var review models.Review
		err := rows.Scan(
			&review.ID,
			&review.CourseCode,
			&review.Email,
			&review.AuthorName,
			&review.Liked,
			&review.Difficulty,
			&review.RealWorldRelevance,
			&review.ReviewText,
			&review.CreatedAt,
			&review.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		reviews = append(reviews, review)
	}

	return reviews, nil
}
