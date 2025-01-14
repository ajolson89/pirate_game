#!/bin/bash

# Exit on error
set -e

# Create a temporary Dockerfile
cat << EOF > Dockerfile.layer
FROM public.ecr.aws/lambda/python:3.9

# Copy requirements file
COPY lambda/requirements-lambda.txt .

# Install dependencies
RUN pip install \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.9 \
    --only-binary=:all: \
    --target /opt/python \
    -r requirements-lambda.txt

# Verify Pydantic installation
RUN ls -la /opt/python/pydantic*

# Create the layer directory structure
RUN mkdir -p /opt/layer/python
RUN cp -r /opt/python/* /opt/layer/python/

# List contents to verify
RUN ls -la /opt/layer/python/
EOF

# Build the Docker image
docker build -t lambda-layer-builder -f Dockerfile.layer .

# Create the layer directory
LAYER_DIR="lambda_layer"
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR"

# Copy the layer from the container
docker run --rm -v "$(pwd)/$LAYER_DIR:/output" lambda-layer-builder cp -r /opt/layer/* /output/

# Verify the contents
echo "Verifying layer contents..."
ls -la "$LAYER_DIR/python/"

# Create zip file
echo "Creating zip file..."
cd "$LAYER_DIR"
zip -r ../lambda_layer.zip .
cd ..

# Clean up
rm Dockerfile.layer

echo "Lambda layer created successfully in lambda_layer.zip"