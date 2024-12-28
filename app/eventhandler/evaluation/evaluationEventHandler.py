from datetime import datetime

from bson import ObjectId
from confluent_kafka.cimpl import Consumer, KafkaError, KafkaException
from deepeval.metrics import ConversationRelevancyMetric, ConversationCompletenessMetric, KnowledgeRetentionMetric
from deepeval.test_case import ConversationalTestCase, LLMTestCase

from app.database import evaluation_collection, chat_room_collection
from app.eventhandler.evaluation.customOllamaLLM import CustomOllamaLLM

KAFKA_BROKER = "localhost:9092"  # Kafka broker address
EVALUATION_TOPIC_NAME = "Evaluation"  # Kafka topic
GROUP_ID = "evaluation-processing-group"  # Consumer group ID

def evaluate_conversation(chat_room_object_id, user_id, chat_room_id, conversation):
    llm_test_cases = get_llm_test_cases(conversation)

    convo_test_case = ConversationalTestCase(
        turns=llm_test_cases
    )

    custom_llm = CustomOllamaLLM()

    relevancy_metric = ConversationRelevancyMetric(threshold=0.5, model=custom_llm)
    completeness_metric = ConversationCompletenessMetric(threshold=0.5, model=custom_llm)
    knowledge_retention_metric = KnowledgeRetentionMetric(threshold=0.5, model=custom_llm)

    relevancy_metric.measure(convo_test_case)
    print(relevancy_metric.score)
    print(relevancy_metric.reason)

    completeness_metric.measure(convo_test_case)
    print(completeness_metric.score)
    print(completeness_metric.reason)

    knowledge_retention_metric.measure(convo_test_case)
    print(knowledge_retention_metric.score)
    print(knowledge_retention_metric.reason)

    persist_metric(chat_room_object_id, user_id, chat_room_id, relevancy_metric, completeness_metric, knowledge_retention_metric)

def persist_metric(
        chat_room_object_id,
        user_id,
chat_room_id,
        relevancy_metric: ConversationRelevancyMetric,
        completeness_metric: ConversationCompletenessMetric,
        knowledge_retention_metric: KnowledgeRetentionMetric):
    metrics_entry = {
        "relevancy_metric_score": relevancy_metric.score,
        "relevancy_metric_reason": relevancy_metric.reason,
        "completeness_metric_score": completeness_metric.score,
        "completeness_metric_reason": completeness_metric.reason,
        "knowledge_retention_metric_score": knowledge_retention_metric.score,
        "knowledge_retention_metric_reason": knowledge_retention_metric.reason,
        "updated_at": datetime.now()
    }

    evaluation_collection.update_one(
        {
            "chat_room_object_id": chat_room_object_id,
            "user_id": user_id,
            "chat_room_id": chat_room_id
        },
        {
            "$setOnInsert": {"created_at": datetime.now()},  # Set createdAt only on insert
            "$set": {"metrics": metrics_entry}
        },
        upsert=True
    )

def get_llm_test_cases(chat_history):
    llm_test_cases = []
    for i in range(len(chat_history) - 1):
        if chat_history[i]['sender_type'] == 'user' and chat_history[i + 1]['sender_type'] == 'assistant':
            input_message = chat_history[i]['message']
            actual_output = chat_history[i + 1]['message']
            llm_test_cases.append(
                LLMTestCase(
                    input=input_message,
                    actual_output=actual_output))

    return llm_test_cases

class EvaluationProcessor:
    def __init__(self):
        # Initialize MongoDB client
        self.collection = evaluation_collection

        # Initialize Kafka consumer
        self.consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True
        })

    def consume_messages(self):
        """Consume messages from Kafka and process the file."""
        self.consumer.subscribe([EVALUATION_TOPIC_NAME])

        print(f"Consuming messages from Kafka topic: {EVALUATION_TOPIC_NAME}")

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
                print(f"Received message in {EVALUATION_TOPIC_NAME}: {message_value}")

                chat_room_object_id = ObjectId(message_value)
                chat_room = chat_room_collection.find_one({"_id": chat_room_object_id})

                evaluate_conversation(
                    chat_room_object_id,
                    chat_room.get('user_id'),
                    chat_room.get('chat_room_id'),
                    chat_room.get('messages'))

        except KeyboardInterrupt:
            print("Kafka consumer interrupted.")
        finally:
            self.consumer.close()

def init_evaluation_event_listener():
    # Evaluation processor
    evaluation_processor = EvaluationProcessor()
    evaluation_processor.consume_messages()