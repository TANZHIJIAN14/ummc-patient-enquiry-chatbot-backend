#!/bin/bash

echo "Setting up environment..."

# Create topic: UploadedFile
kafka-topics.sh --create --topic UploadedFile --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
echo "Topic 'UploadedFile' created."

# Create topic: DeletedFile
kafka-topics.sh --create --topic DeletedFile --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
echo "Topic 'DeletedFile' created."

# Create topic: FeedbackAnalysis
kafka-topics.sh --create --topic FeedbackAnalysis --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
echo "Topic 'FeedbackAnalysis' created."

echo "Environment setup complete!"