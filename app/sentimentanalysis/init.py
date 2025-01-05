from transformers import pipeline

def sentiment_analysis(message):
    sentiment_pipeline = pipeline(
        "text-classification",
        "finiteautomata/bertweet-base-sentiment-analysis")
    data = [message]
    result = sentiment_pipeline(data)

    # Map the labels to full words
    label_mapping = {
        "POS": "POSITIVE",
        "NEU": "NEUTRAL",
        "NEG": "NEGATIVE"
    }

    print(f"Sentiment analysis result: {result}")
    # Convert the label
    result_label = label_mapping.get(result[0]['label'], "unknown")
    return result_label