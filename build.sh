#!/bin/bash

# Build script for FabrikaTroliv Telegram Bot
# Usage: ./build.sh [tag]

# Default tag is "latest" if not provided
TAG=${1:-latest}
IMAGE_NAME="fabrika-troliv"

echo "Building Docker image: ${IMAGE_NAME}:${TAG}"

# Build the Docker image
docker build -t ${IMAGE_NAME}:${TAG} .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Build successful! Your image is ready: ${IMAGE_NAME}:${TAG}"
    echo ""
    echo "To run the container:"
    echo "docker run -d --name fabrika-troliv ${IMAGE_NAME}:${TAG}"
    echo ""
    echo "To view logs:"
    echo "docker logs -f fabrika-troliv"
else
    echo "❌ Build failed!"
fi
