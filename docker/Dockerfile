# Golang
FROM golang:1.20

# Environment variables
ENV GO111MODULE=on \
    CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64

# Set working directory
WORKDIR /app

# Copy go.mod and go.sum to container
COPY go.mod go.sum /

# Download dependencies
RUN go mod download

# Copy source code into container
COPY . .

# Build Go application
RUN go build -o main .

# Port to run on
EXPOSE 8080

# Command to start application
CMD ["./main"]
