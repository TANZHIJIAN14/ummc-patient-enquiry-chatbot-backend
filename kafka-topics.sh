#!/bin/bash

echo "Setting up environment..."
# Example commands
kafka-topics.sh --create --topic UploadedFile --bootstrap-server localhost:9092
echo "Environment setup complete!"