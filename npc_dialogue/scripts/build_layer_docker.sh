#!/bin/bash

# Exit on error
set -e

echo "Starting Lambda layer build process..."

# Create a temporary Dockerfile
cat << EOF > Dockerfile.layer
FROM public.ecr.aws/lambda/python:3.9

WORKDIR /opt

# Copy requirements file
COPY lambda/requirements-lambda.txt .

# Install dependencies directly into python directory
RUN mkdir -p /opt/python && \
    pip install \
    --no-cache-dir \
    --platform manylinux2014_x86_64 \
    --target /opt/python \
    --implementation cp \
    --python-version 3.9 \
    --only-binary=:all: \
    pydantic==2.6.1 \
    aws-lambda-powertools==2.32.0 \
    aws-xray-sdk==2.12.1 \
    boto3==1.28.0 \
    python-json-logger==2.0.7 \
    typing-extensions>=4.5.0

# Verify pydantic installation
RUN ls -la /opt/python/pydantic*
RUN python3 -c "import sys; sys.path.append('/opt/python'); import pydantic; print(f'Pydantic version: {pydantic.__version__}')"

EOF

echo "Building Docker image..."
# Build the Docker image
docker build -t lambda-layer-builder -f Dockerfile.layer .

echo "Creating layer directory..."
# Create the layer directory
LAYER_DIR="lambda_layer"
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR/python"

echo "Copying files from Docker container..."
# Create a temporary container and copy files
CONTAINER_ID=$(docker create lambda-layer-builder)
docker cp $CONTAINER_ID:/opt/python/. "$LAYER_DIR/python/"
docker rm $CONTAINER_ID

echo "Verifying layer contents..."
# Verify the contents
ls -la "$LAYER_DIR/python/"

echo "Creating zip file..."
# Create zip file (important: zip the contents, not the directory)
cd "$LAYER_DIR"
zip -r ../lambda_layer.zip python/
cd ..

# Verify the zip contents
echo "Verifying zip contents:"
unzip -l lambda_layer.zip | grep pydantic

# Clean up
rm Dockerfile.layer

echo "Lambda layer zip created successfully at lambda_layer.zip"