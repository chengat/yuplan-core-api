package handlers

import (
	"net/http"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
)

type SectionHandler struct {
	repo repository.SectionRepositoryInterface
}

func NewSectionHandler(repo repository.SectionRepositoryInterface) *SectionHandler {
	return &SectionHandler{repo: repo}
}

func (h *SectionHandler) GetSectionsByCourseID(c *gin.Context) {
	courseID := c.Param("course_id")

	sections, err := h.repo.GetByCourseID(c.Request.Context(), courseID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch sections"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  sections,
		"count": len(sections),
	})
}
