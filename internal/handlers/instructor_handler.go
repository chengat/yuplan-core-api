package handlers

import (
	"net/http"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
)

type InstructorHandler struct {
	repo repository.InstructorRepositoryInterface
}

func NewInstructorHandler(repo repository.InstructorRepositoryInterface) *InstructorHandler {
	return &InstructorHandler{repo: repo}
}

func (h *InstructorHandler) GetInstructorsByCourseID(c *gin.Context) {
	courseID := c.Param("course_id")

	instructors, err := h.repo.GetByCourseID(c.Request.Context(), courseID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch instructors"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  instructors,
		"count": len(instructors),
	})
}

