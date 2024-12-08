from confluent_kafka import Consumer, KafkaError, KafkaException

from app.database import uploaded_file_collection
from app.pinecone import delete_file

KAFKA_BROKER = "localhost:9092"  # Kafka broker address
DELETED_FILE_TOPIC_NAME = "DeletedFile"  # Kafka topic
GROUP_ID = "delete-file-processing-group"  # Consumer group ID

class DeleteFileProcessor:
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

    def consume_messages(self):
        """Consume messages from Kafka and process the file."""
        self.consumer.subscribe([DELETED_FILE_TOPIC_NAME])

        print(f"Consuming messages from Kafka topic: {DELETED_FILE_TOPIC_NAME}")

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
                pinecone_file_id = message_value.strip()  # File ID

                response = delete_file(pinecone_file_id)

                if response.status_code != 200:
                    raise Exception(f"Failed to delete file in pinecone with ID: {pinecone_file_id}")

                print("Successfully deleted file in pinecone")

        except KeyboardInterrupt:
            print("Kafka consumer interrupted.")
        finally:
            self.consumer.close()

def init_delete_file_event_listener():
    # Delete file processor
    delete_processor = DeleteFileProcessor()
    delete_processor.consume_messages()