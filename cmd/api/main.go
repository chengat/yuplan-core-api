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
	sectionActivityRepo := repository.NewSectionActivityRepository(pool)
	sectionRepo := repository.NewSectionRepository(pool, sectionActivityRepo)
	courseHandler := handlers.NewCourseHandler(courseRepo, sectionRepo)

	instructorRepo := repository.NewInstructorRepository(pool)
	instructorHandler := handlers.NewInstructorHandler(instructorRepo)

	sectionHandler := handlers.NewSectionHandler(sectionRepo)

	router := gin.Default()
	api := router.Group("/api/v1")
	{
		api.GET("/courses", courseHandler.GetCourses)
		api.GET("/courses/paginated", courseHandler.GetPaginatedCourses)
		api.GET("/courses/search", courseHandler.SearchCourses)
		api.GET("/courses/:course_code", courseHandler.GetCoursesByCode)
		api.GET("/instructors/:course_id", instructorHandler.GetInstructorsByCourseID)
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
