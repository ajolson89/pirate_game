#!/bin/bash

# Exit on error
set -e

# Create a temporary directory
TEMP_DIR="$(mktemp -d)"
echo "Created temporary directory: $TEMP_DIR"

# Create the Python directory structure
mkdir -p "$TEMP_DIR/python"

# Install dependencies using pre-built wheels
pip install \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.9 \
    --only-binary=:all: \
    --target "$LAYER_DIR/python" \
    aws-lambda-powertools==2.32.0 \
    aws-xray-sdk==2.12.1 \
    boto3==1.28.0 \
    pydantic==2.6.1 \
    python-json-logger==2.0.7

# Create the layer directory
LAYER_DIR="lambda_layer"
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR"

# Move the installed packages to the layer directory
cp -r "$TEMP_DIR/python" "$LAYER_DIR/"

# Clean up the temporary directory
rm -rf "$TEMP_DIR"

echo "Lambda layer created successfully in $LAYER_DIR"