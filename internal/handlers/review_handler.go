package handlers

import (
	"net/http"
	"strconv"
	"yuplan/internal/models"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
)

type ReviewHandler struct {
	repo repository.ReviewRepositoryInterface
}

func NewReviewHandler(repo repository.ReviewRepositoryInterface) *ReviewHandler {
	return &ReviewHandler{
		repo: repo,
	}
}

// CreateReview handles POST /api/v1/courses/:course_code/reviews
func (h *ReviewHandler) CreateReview(c *gin.Context) {
	courseCode := c.Param("course_code")
	
	var req models.CreateReviewRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	review := &models.Review{
		CourseCode:         courseCode,
		Email:              req.Email,
		AuthorName:         req.AuthorName,
		Liked:              req.Liked,
		Difficulty:         req.Difficulty,
		RealWorldRelevance: req.RealWorldRelevance,
		ReviewText:         req.ReviewText,
	}

	if err := h.repo.Create(c.Request.Context(), review); err != nil {
		// Check for duplicate review (UNIQUE constraint violation)
		if err.Error() == "ERROR: duplicate key value violates unique constraint \"reviews_course_code_email_key\" (SQLSTATE 23505)" {
			c.JSON(http.StatusConflict, gin.H{"error": "You have already submitted a review for this course"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create review"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"data":    review,
		"message": "Review created successfully",
	})
}

// GetReviews handles GET /api/v1/courses/:course_code/reviews
func (h *ReviewHandler) GetReviews(c *gin.Context) {
	courseCode := c.Param("course_code")
	
	// Parse query parameters
	sortBy := c.DefaultQuery("sort", "recent") // "recent" or "earliest"
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
	
	// Validate limit
	if limit < 1 || limit > 50 {
		limit = 10
	}
	
	reviews, err := h.repo.GetByCourseCode(c.Request.Context(), courseCode, sortBy, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch reviews"})
		return
	}
	
	// Get course stats
	stats, err := h.repo.GetCourseStats(c.Request.Context(), courseCode)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch course stats"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  reviews,
		"count": len(reviews),
		"stats": stats,
	})
}
