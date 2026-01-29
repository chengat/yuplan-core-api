package repository

import (
	"context"
	"testing"
	"time"
	"yuplan/internal/models"

	"github.com/pashagolub/pgxmock"
	"github.com/stretchr/testify/assert"
)

func TestReviewRepository_Create(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewReviewRepository(mock)
	ctx := context.Background()

	reviewText := "Great course!"
	authorName := "John Smith"
	review := &models.Review{
		CourseCode:         "EECS2030",
		Email:              "student@yorku.ca",
		AuthorName:         &authorName,
		Liked:              true,
		Difficulty:         3,
		RealWorldRelevance: 5,
		ReviewText:         &reviewText,
	}

	now := time.Now()
	mock.ExpectQuery("INSERT INTO reviews").
		WithArgs(
			review.CourseCode,
			review.Email,
			review.AuthorName,
			review.Liked,
			review.Difficulty,
			review.RealWorldRelevance,
			review.ReviewText,
			pgxmock.AnyArg(), // created_at
			pgxmock.AnyArg(), // updated_at
		).
		WillReturnRows(pgxmock.NewRows([]string{"id"}).AddRow("test-review-id"))

	err = repo.Create(ctx, review)
	assert.NoError(t, err)
	assert.Equal(t, "test-review-id", review.ID)
	assert.False(t, review.CreatedAt.IsZero())
	assert.False(t, review.UpdatedAt.IsZero())
	assert.NoError(t, mock.ExpectationsWereMet())

	// Check that created_at and updated_at are around now
	assert.WithinDuration(t, now, review.CreatedAt, 5*time.Second)
	assert.WithinDuration(t, now, review.UpdatedAt, 5*time.Second)
}

func TestReviewRepository_CreateAnonymous(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewReviewRepository(mock)
	ctx := context.Background()

	reviewText := "Great course!"
	review := &models.Review{
		CourseCode:         "EECS2030",
		Email:              "student@yorku.ca",
		AuthorName:         nil, // Anonymous
		Liked:              true,
		Difficulty:         3,
		RealWorldRelevance: 5,
		ReviewText:         &reviewText,
	}

	mock.ExpectQuery("INSERT INTO reviews").
		WithArgs(
			review.CourseCode,
			review.Email,
			pgxmock.AnyArg(), // author_name (nil pointer)
			review.Liked,
			review.Difficulty,
			review.RealWorldRelevance,
			review.ReviewText,
			pgxmock.AnyArg(), // created_at
			pgxmock.AnyArg(), // updated_at
		).
		WillReturnRows(pgxmock.NewRows([]string{"id"}).AddRow("test-review-id"))

	err = repo.Create(ctx, review)
	assert.NoError(t, err)
	assert.Equal(t, "test-review-id", review.ID)
	assert.Nil(t, review.AuthorName)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestReviewRepository_GetByCourseCode(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewReviewRepository(mock)
	ctx := context.Background()

	courseCode := "EECS2030"
	now := time.Now()
	reviewText := "Great course!"
	authorName := "John Smith"

	rows := pgxmock.NewRows([]string{
		"id", "course_code", "email", "author_name", "liked", "difficulty", "real_world_relevance",
		"review_text", "created_at", "updated_at",
	}).
		AddRow(
			"review-1", courseCode, "student1@yorku.ca", &authorName, true, 3, 5,
			&reviewText, now, now,
		).
		AddRow(
			"review-2", courseCode, "student2@yorku.ca", nil, true, 4, 4,
			&reviewText, now.Add(-1*time.Hour), now.Add(-1*time.Hour),
		)

	mock.ExpectQuery("SELECT(.+)FROM reviews(.+)WHERE course_code = (.+)ORDER BY created_at DESC").
		WithArgs(courseCode, 10, 0).
		WillReturnRows(rows)

	reviews, err := repo.GetByCourseCode(ctx, courseCode, "recent", 10, 0)
	assert.NoError(t, err)
	assert.Len(t, reviews, 2)
	assert.Equal(t, "review-1", reviews[0].ID)
	assert.NotNil(t, reviews[0].AuthorName)
	assert.Equal(t, "John Smith", *reviews[0].AuthorName)
	assert.Nil(t, reviews[1].AuthorName) // Anonymous
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestReviewRepository_GetByCourseCode_WithEarliestSort(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewReviewRepository(mock)
	ctx := context.Background()

	courseCode := "EECS2030"
	now := time.Now()
	reviewText := "Great course!"

	rows := pgxmock.NewRows([]string{
		"id", "course_code", "email", "author_name", "liked", "difficulty", "real_world_relevance",
		"review_text", "created_at", "updated_at",
	}).
		AddRow(
			"review-1", courseCode, "student1@yorku.ca", nil, true, 3, 5,
			&reviewText, now.Add(-2*time.Hour), now.Add(-2*time.Hour),
		).
		AddRow(
			"review-2", courseCode, "student2@yorku.ca", nil, true, 4, 4,
			&reviewText, now, now,
		)

	mock.ExpectQuery("SELECT(.+)FROM reviews(.+)WHERE course_code = (.+)ORDER BY created_at ASC").
		WithArgs(courseCode, 10, 0).
		WillReturnRows(rows)

	reviews, err := repo.GetByCourseCode(ctx, courseCode, "earliest", 10, 0)
	assert.NoError(t, err)
	assert.Len(t, reviews, 2)
	assert.Equal(t, "review-1", reviews[0].ID)
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestReviewRepository_GetCourseStats(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewReviewRepository(mock)
	ctx := context.Background()

	courseCode := "EECS2030"

	rows := pgxmock.NewRows([]string{
		"total_reviews", "likes", "dislikes", "avg_difficulty", "avg_real_world_relevance",
	}).AddRow(10, 7, 3, 3.5, 4.2)

	mock.ExpectQuery("SELECT(.+)FROM reviews(.+)WHERE course_code = (.+)").
		WithArgs(courseCode).
		WillReturnRows(rows)

	stats, err := repo.GetCourseStats(ctx, courseCode)
	assert.NoError(t, err)
	assert.Equal(t, 10, stats["total_reviews"])
	assert.Equal(t, 7, stats["likes"])
	assert.Equal(t, 3, stats["dislikes"])
	assert.Equal(t, 70, stats["like_percentage"])
	assert.Equal(t, 3.5, stats["avg_difficulty"])
	assert.Equal(t, 4.2, stats["avg_real_world_relevance"])
	assert.NoError(t, mock.ExpectationsWereMet())
}

func TestReviewRepository_GetAll(t *testing.T) {
	mock, err := pgxmock.NewPool()
	assert.NoError(t, err)
	defer mock.Close()

	repo := NewReviewRepository(mock)
	ctx := context.Background()

	now := time.Now()
	reviewText := "Great course!"
	authorName := "John Smith"

	rows := pgxmock.NewRows([]string{
		"id", "course_code", "email", "author_name", "liked", "difficulty", "real_world_relevance",
		"review_text", "created_at", "updated_at",
	}).
		AddRow(
			"review-1", "EECS2030", "student1@yorku.ca", &authorName, true, 3, 5,
			&reviewText, now, now,
		).
		AddRow(
			"review-2", "EECS3101", "student2@yorku.ca", nil, false, 4, 3,
			&reviewText, now.Add(-1*time.Hour), now.Add(-1*time.Hour),
		).
		AddRow(
			"review-3", "EECS2030", "student3@yorku.ca", &authorName, true, 2, 4,
			&reviewText, now.Add(-2*time.Hour), now.Add(-2*time.Hour),
		)

	mock.ExpectQuery("SELECT(.+)FROM reviews(.+)ORDER BY created_at DESC").
		WillReturnRows(rows)

	reviews, err := repo.GetAll(ctx)
	assert.NoError(t, err)
	assert.Len(t, reviews, 3)
	assert.Equal(t, "review-1", reviews[0].ID)
	assert.Equal(t, "EECS2030", reviews[0].CourseCode)
	assert.NotNil(t, reviews[0].AuthorName)
	assert.Equal(t, "review-2", reviews[1].ID)
	assert.Equal(t, "EECS3101", reviews[1].CourseCode)
	assert.Nil(t, reviews[1].AuthorName) // Anonymous
	assert.Equal(t, "review-3", reviews[2].ID)
	assert.NoError(t, mock.ExpectationsWereMet())
}
