package handlers

import (
	"net/http"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
)

type TutorialHandler struct {
	repo repository.TutorialRepositoryInterface
}

func NewTutorialHandler(repo repository.TutorialRepositoryInterface) *TutorialHandler {
	return &TutorialHandler{repo: repo}
}

func (h *TutorialHandler) GetTutorialsBySectionID(c *gin.Context) {
	sectionID := c.Param("section_id")

	tutorials, err := h.repo.GetBySectionID(c.Request.Context(), sectionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch tutorials"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  tutorials,
		"count": len(tutorials),
	})
}
