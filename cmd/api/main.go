package main

import (
	"context"
	"log"
	"yuplan/internal/config"
	"yuplan/internal/database"
	"yuplan/internal/handlers"
	"yuplan/internal/repository"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v4/pgxpool"
)

func main() {
	ctx := context.Background()
	cfg := config.Load()

	pool, err := initDatabase(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer pool.Close()

	router := setupRouter(pool)

	if err := startServer(router, cfg.Port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

func initDatabase(ctx context.Context, databaseURL string) (*pgxpool.Pool, error) {
	pool, err := database.NewPool(ctx, databaseURL)
	if err != nil {
		return nil, err
	}
	return pool, nil
}

func setupRouter(pool *pgxpool.Pool) *gin.Engine {
	courseRepo := repository.NewCourseRepository(pool)
	courseHandler := handlers.NewCourseHandler(courseRepo)

	instructorRepo := repository.NewInstructorRepository(pool)
	instructorHandler := handlers.NewInstructorHandler(instructorRepo)

	labRepo := repository.NewLabRepository(pool)
	labHandler := handlers.NewLabHandler(labRepo)

	sectionRepo := repository.NewSectionRepository(pool)
	sectionHandler := handlers.NewSectionHandler(sectionRepo)

	tutorialRepo := repository.NewTutorialRepository(pool)
	tutorialHandler := handlers.NewTutorialHandler(tutorialRepo)

	router := gin.Default()
	api := router.Group("/api/v1")
	{
		api.GET("/courses", courseHandler.GetCourses)
		api.GET("/courses/search", courseHandler.SearchCourses)
		api.GET("/courses/:course_id", courseHandler.GetCourseByID)
		api.GET("/instructors/:course_id", instructorHandler.GetInstructorsByCourseID)
		api.GET("/labs/:section_id", labHandler.GetLabsBySectionID)
		api.GET("/tutorials/:section_id", tutorialHandler.GetTutorialsBySectionID)
		api.GET("/sections/:course_id", sectionHandler.GetSectionsByCourseID)
	}
	return router
}

func startServer(router *gin.Engine, port string) error {
	log.Printf("Starting server on port %s", port)
	if err := router.Run(":" + port); err != nil {
		return err
	}
	return nil
}
