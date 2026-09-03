FROM golang:1.23
RUN go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
WORKDIR /workspace
