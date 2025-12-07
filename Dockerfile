FROM golang:1.24-alpine

# Install dependencies
RUN apk add --no-cache \
    postgresql-client \
    bash \
    curl

# Install golang-migrate
RUN curl -L https://github.com/golang-migrate/migrate/releases/download/v4.19.0/migrate.linux-amd64.tar.gz | tar xvz && \
    mv migrate /usr/local/bin/migrate && \
    chmod +x /usr/local/bin/migrate

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN chmod +x scripts/*.sh

EXPOSE 8080

CMD ["go", "run", "cmd/api/main.go"]