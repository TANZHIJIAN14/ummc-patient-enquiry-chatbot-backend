from transformers import pipeline

def sentiment_analysis(message):
    sentiment_pipeline = pipeline("sentiment-analysis")
    data = [message]
    result = sentiment_pipeline(data)
    print(f"Sentiment analysis result: {result}")
    return result[0]['label']