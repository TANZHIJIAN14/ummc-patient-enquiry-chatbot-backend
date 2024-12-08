from confluent_kafka import Consumer, KafkaException, KafkaError
from bson import ObjectId
from app.database import uploaded_file_collection
from app.eventhandler.kafkaConfig import TOPIC_MAP
from app.pinecone import upload_file

# Kafka configuration
KAFKA_BROKER = "localhost:9092"  # Kafka broker address
TOPIC_NAME = TOPIC_MAP["uploaded-file"]  # Kafka topic
GROUP_ID = "file-processing-group"  # Consumer group ID

def upload_file_to_assistance(file_doc):
    """Process the file."""
    file_name = file_doc["filename"]
    file_data = file_doc["file_data"]

    print(file_name)
    response = upload_file(file_name, file_data)
    if response is None:
        raise Exception("Failed to upload file to pinecone assistant")

    print(f"Successfully upload file to pinecone assistant: {response.json()}")
    return response["id"]


class FileProcessor:
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

    def get_file_by_id(self, file_id):
        """Retrieve the file from MongoDB by its ID."""
        try:
            file_doc = self.collection.find_one({"_id": ObjectId(file_id)})
            if not file_doc:
                print(f"File with ID {file_id} not found.")
                return None

            return file_doc
        except Exception as e:
            print(f"Error retrieving file from MongoDB: {e}")
            return None

    def consume_messages(self):
        """Consume messages from Kafka and process the file."""
        self.consumer.subscribe([TOPIC_NAME])

        print(f"Consuming messages from Kafka topic: {TOPIC_NAME}")

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
                file_id = message_value.strip()  # File ID

                # Retrieve and process the file
                file_doc = self.get_file_by_id(file_id)
                if file_doc:
                    uploaded_file_id = upload_file_to_assistance(file_doc)
                    # Query the record by its ID
                    query = {"_id": file_id}
                    update = {
                        "$set": {
                            "uploaded_file_id": uploaded_file_id  # Add or update the uploaded_file_id
                        }
                    }
                    self.collection.update_one(query, update, upsert=True)


        except KeyboardInterrupt:
            print("Kafka consumer interrupted.")
        finally:
            self.consumer.close()

def init_event_listener():
    processor = FileProcessor()
    processor.consume_messages()