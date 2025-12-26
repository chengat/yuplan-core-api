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
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	courses, err := h.repo.GetAllRandomized(c.Request.Context(), limit, offset)
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
