#!/bin/bash

# Exit on error
set -e

echo "Building Lambda layer..."
./scripts/build_layer_docker.sh

echo "Zipping Lambda layer..."
./scripts/zip_layer.sh

echo "Deploying stack..."
cdk deploy