package handlers

import (
	"net/http"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
)

type LabHandler struct {
	repo repository.LabRepositoryInterface
}

func NewLabHandler(repo repository.LabRepositoryInterface) *LabHandler {
	return &LabHandler{repo: repo}
}

func (h *LabHandler) GetLabsBySectionID(c *gin.Context) {
	sectionID := c.Param("section_id")

	labs, err := h.repo.GetBySectionID(c.Request.Context(), sectionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch labs"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  labs,
		"count": len(labs),
	})
}
