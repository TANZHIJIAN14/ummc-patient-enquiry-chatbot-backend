# Kafka configuration
from confluent_kafka import Producer

from app.config import config

KAFKA_BROKER = config("KAFKA_BROKER") # Replace with your Kafka broker address

# Create a Kafka producer
producer = Producer({"bootstrap.servers": KAFKA_BROKER})

def delivery_report(err, msg):
    """Callback to confirm delivery."""
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


def produce_message(topic, key, value):
    try:
        # Produce a message to the Kafka topic
        producer.produce(
            topic,
            key=key,
            value=str(value).encode('utf-8'),
            callback=delivery_report,
        )
        # Flush to ensure the message is sent
        producer.flush()
        print(f"Successfully publish {topic} event with ID: {value}")
    except Exception as e:
        print(f"Failed to produce message: {e}")