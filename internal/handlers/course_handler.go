package handlers

import (
	"net/http"
	"strconv"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
)

type CourseHandler struct {
	repo repository.CourseRepositoryInterface
}

func NewCourseHandler(repo repository.CourseRepositoryInterface) *CourseHandler {
	return &CourseHandler{repo: repo}
}

func (h *CourseHandler) GetCourses(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "20"))

	courses, err := h.repo.GetRandomCourses(c.Request.Context(), limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch courses"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  courses,
		"count": len(courses),
	})
}

func (h *CourseHandler) GetCourseByID(c *gin.Context) {
	courseID := c.Param("course_id")

	course, err := h.repo.GetByID(c.Request.Context(), courseID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Course not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": course})
}

func (h *CourseHandler) SearchCourses(c *gin.Context) {
	query := c.Query("q")
	if query == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Query parameter 'q' is required"})
		return
	}

	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	courses, err := h.repo.Search(c.Request.Context(), query, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to search courses"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  courses,
		"count": len(courses),
	})
}

// GetPaginatedCourses handles paginated course requests with optional filtering
func (h *CourseHandler) GetPaginatedCourses(c *gin.Context) {
	// Parse pagination parameters
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "20"))
	
	// Validate pagination parameters
	if page < 1 {
		page = 1
	}
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}
	
	// Parse optional filter parameters
	var faculty *string
	if f := c.Query("faculty"); f != "" {
		faculty = &f
	}
	
	var courseCodeRange *string
	if ccr := c.Query("course_code_range"); ccr != "" {
		courseCodeRange = &ccr
	}
	
	// Get total count for pagination metadata
	totalCount, err := h.repo.GetCoursesCount(c.Request.Context(), faculty, courseCodeRange)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch course count"})
		return
	}
	
	// Calculate total pages
	totalPages := (totalCount + pageSize - 1) / pageSize
	if totalPages == 0 {
		totalPages = 1
	}
	
	// Get paginated courses
	courses, err := h.repo.GetPaginatedCourses(c.Request.Context(), page, pageSize, faculty, courseCodeRange)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch courses"})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"data":        courses,
		"page":        page,
		"page_size":   pageSize,
		"total_items": totalCount,
		"total_pages": totalPages,
	})
}
