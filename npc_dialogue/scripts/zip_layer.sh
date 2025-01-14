#!/bin/bash

# Exit on error
set -e

# Remove old zip if it exists
rm -f lambda_layer.zip

# Change to lambda_layer directory
cd lambda_layer

# Zip the contents
zip -r ../lambda_layer.zip .

# Go back to original directory
cd ..

echo "Created lambda_layer.zip"