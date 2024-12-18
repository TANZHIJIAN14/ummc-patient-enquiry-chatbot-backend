import time
from http import HTTPStatus

import requests
from confluent_kafka import Consumer, KafkaException, KafkaError
from bson import ObjectId
from app.database import uploaded_file_collection
from app.pinecone import upload_file, subscribe_file

# Kafka configuration
KAFKA_BROKER = "localhost:9092"  # Kafka broker address
UPLOADED_FILE_TOPIC_NAME = "UploadedFile"  # Kafka topic
GROUP_ID = "file-processing-group"  # Consumer group ID

def upload_file_to_assistance(file_doc):
    """Process the file."""
    file_name = file_doc["filename"]
    file_data = file_doc["file_data"]

    print(file_name)
    response = upload_file(file_name, file_data)
    if response.status_code != HTTPStatus.OK.value:
        raise Exception(f"Failed to upload file to pinecone assistant: {response.json()}")

    print(f"Successfully upload file to pinecone assistant: {response.json()}")
    return response.json()["id"]

def poll_subscription_status(mongodb_file_id, max_attempts=20, delay=5):
    for attempt in range(max_attempts):
        try:
            response = subscribe_file(mongodb_file_id)  # Set the timeout here
            response.raise_for_status()  # Raise an error for failed requests
            status = response.json() # Assuming the response contains a JSON payload with status info

            print(f"Attempt {attempt + 1}: Status - {status}")

            # Check if the desired condition is met
            if status.get("status") != "Processing":
                return status

        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1}: Request timed out.")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}: An error occurred - {e}")

        # Wait for the next polling attempt
        time.sleep(delay)

    raise TimeoutError(f"Polling timed out after {max_attempts} attempts.")


class UploadFileProcessor:
    def __init__(self):
        # Initialize MongoDB client
        self.collection = uploaded_file_collection

        # Initialize Kafka consumer
        self.consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True
        })

    def get_file_by_id(self, mongodb_file_id):
        """Retrieve the file from MongoDB by its ID."""
        try:
            file_doc = self.collection.find_one({"_id": ObjectId(mongodb_file_id)})
            if not file_doc:
                print(f"File with ID {mongodb_file_id} not found.")
                return None

            return file_doc
        except Exception as e:
            print(f"Error retrieving file from MongoDB: {e}")
            return None

    def consume_messages(self):
        """Consume messages from Kafka and process the file."""
        self.consumer.subscribe([UPLOADED_FILE_TOPIC_NAME])

        print(f"Consuming messages from Kafka topic: {UPLOADED_FILE_TOPIC_NAME}")

        try:
            while True:
                msg = self.consumer.poll(1.0)  # Poll for messages

                if msg is None:
                    continue  # No messages
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event, ignore
                        continue
                    else:
                        raise KafkaException(msg.error())

                # Decode message
                message_value = msg.value().decode("utf-8")
                print(f"Received message: {message_value}")

                # Assume the message contains the file ID
                mongodb_file_id = message_value.strip()  # File ID

                # Retrieve and process the file
                file_doc = self.get_file_by_id(mongodb_file_id)
                if file_doc:
                    uploaded_file_id = upload_file_to_assistance(file_doc)
                    metadata = poll_subscription_status(uploaded_file_id)

                    # Convert mongodb_file_id to ObjectId
                    object_id = ObjectId(mongodb_file_id)

                    # Query the record by its ID
                    query = {"_id": object_id}
                    update = {
                        "$set": {
                            "uploaded_file_id": uploaded_file_id,
                            "status": metadata["status"],
                            "metadata": metadata
                        }
                    }
                    self.collection.update_one(query, update, upsert=True)
        except KeyboardInterrupt:
            print("Kafka consumer interrupted.")
        finally:
            self.consumer.close()

def init_upload_file_event_listener():
    # Upload file processor
    upload_processor = UploadFileProcessor()
    upload_processor.consume_messages()