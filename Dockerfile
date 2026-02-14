FROM golang:1.24-alpine AS builder

# Install dependencies for building
RUN apk add --no-cache \
    git

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /app/bin/api ./cmd/api/main.go

# Final stage
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache \
    postgresql-client \
    bash \
    curl \
    ca-certificates

# Install golang-migrate
RUN curl -L https://github.com/golang-migrate/migrate/releases/download/v4.19.0/migrate.linux-amd64.tar.gz | tar xvz && \
    mv migrate /usr/local/bin/migrate && \
    chmod +x /usr/local/bin/migrate

WORKDIR /app

# Copy the binary from builder
COPY --from=builder /app/bin/api /app/bin/api

# Copy scripts and other necessary files
COPY scripts/ ./scripts/
COPY migrations/ ./migrations/
COPY db/ ./db/

RUN chmod +x scripts/*.sh && \
    chmod +x /app/bin/api

EXPOSE 8080

# Start: migrations, then selective seed (only seed tables; reviews untouched when seed.sql changes).
CMD ["./scripts/start.sh"]