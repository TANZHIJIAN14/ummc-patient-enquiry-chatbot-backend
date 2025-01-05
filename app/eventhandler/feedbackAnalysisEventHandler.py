from bson import ObjectId
from confluent_kafka import Consumer

from app.database import feedback_collection
from app.sentimentanalysis.init import sentiment_analysis

KAFKA_BROKER = "localhost:9092"  # Kafka broker address
FEEDBACK_ANALYSIS_TOPIC_NAME = "FeedbackAnalysis"  # Kafka topic
GROUP_ID = "feedback-analysis-processing-group"  # Consumer group ID

class FeedbackAnalysisProcessor:
    def __init__(self):
        # Initialize MongoDB client
        self.collection = feedback_collection

        # Initialize Kafka consumer
        self.consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True
        })
        
    def consume_messages(self):
        """Consume messages from Kafka and process the file."""
        self.consumer.subscribe([FEEDBACK_ANALYSIS_TOPIC_NAME])

        print(f"Consuming messages from Kafka topic: {FEEDBACK_ANALYSIS_TOPIC_NAME}")

        try:
            while True:
                msg = self.consumer.poll(1.0)  # Poll for messages

                if msg is None:
                    continue  # No messages

                # Decode message
                message_value = msg.value().decode("utf-8")
                print(f"Received message in {FEEDBACK_ANALYSIS_TOPIC_NAME}: {message_value}")

                query = {"_id": ObjectId(message_value)}
                feedback = self.collection.find_one(query)

                message = feedback["message"]
                analysis_result = sentiment_analysis(message)

                self.collection.update_one(
                    {"_id": ObjectId(message_value)},  # Filter to match the document
                    {"$set": {"label": analysis_result}}  # Update operation
                )

        except KeyboardInterrupt:
            print("Kafka consumer interrupted.")
        except AttributeError as e:
            print(f"Attribute error: {str(e)}")
        except Exception as e:
            print(f"Error consuming event of Feedback Analysis topic: {e}")
        finally:
            self.consumer.close()

def init_feedback_analysis_event_listener():
    # Delete file processor
    feedback_analysis_processor = FeedbackAnalysisProcessor()
    feedback_analysis_processor.consume_messages()