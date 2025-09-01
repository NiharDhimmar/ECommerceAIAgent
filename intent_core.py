# intent_core.py
import os, json, numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Embedding, GlobalAveragePooling1D, Dense
from tensorflow.keras.preprocessing.text import Tokenizer, tokenizer_from_json
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re
from collections import Counter
from datetime import datetime

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE      = os.path.join(BASE_DIR, "intent_model.keras")
TOKENIZER_PATH  = os.path.join(BASE_DIR, "tokenizer.json")
LABELS_PATH     = os.path.join(BASE_DIR, "labels.json")

# ---------- globals (populated on first import / train) ----------
model = None
tokenizer = None
index_label = {}
maxlen = 20    # default – overwritten after training

# Intent categories for conversation analysis
INTENT_CATEGORIES = {
    'customer_service': [
        'speak to agent', 'human agent', 'customer service', 'customer support',
        'representative', 'operator', 'live person', 'talk to someone',
        'help desk', 'service desk', 'customer care', 'support team'
    ],
    'order_management': [
        'place order', 'cancel order', 'modify order', 'track order',
        'order status', 'shipping', 'delivery', 'return', 'refund',
        'invoice', 'payment', 'checkout', 'cart', 'purchase'
    ],
    'product_inquiry': [
        'product information', 'specifications', 'features', 'availability',
        'price', 'cost', 'discount', 'promotion', 'catalog', 'inventory'
    ],
    'technical_support': [
        'technical issue', 'bug', 'error', 'problem', 'not working',
        'troubleshoot', 'fix', 'repair', 'maintenance', 'update'
    ],
    'account_management': [
        'account', 'login', 'password', 'profile', 'settings',
        'registration', 'sign up', 'verification', 'security'
    ],
    'complaint': [
        'complaint', 'dissatisfied', 'unhappy', 'poor service', 'bad experience',
        'issue', 'problem', 'concern', 'feedback', 'review'
    ],
    'general_inquiry': [
        'information', 'question', 'help', 'assistance', 'guidance',
        'how to', 'what is', 'when', 'where', 'why'
    ]
}

# Sentiment keywords
SENTIMENT_KEYWORDS = {
    'positive': [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'satisfied', 'happy', 'pleased', 'love', 'like', 'perfect',
        'helpful', 'useful', 'working', 'solved', 'fixed'
    ],
    'negative': [
        'bad', 'terrible', 'awful', 'horrible', 'disappointed', 'frustrated',
        'angry', 'upset', 'annoyed', 'hate', 'dislike', 'broken',
        'useless', 'waste', 'problem', 'issue', 'error', 'failed'
    ],
    'neutral': [
        'okay', 'fine', 'alright', 'normal', 'standard', 'regular',
        'average', 'mediocre', 'acceptable', 'satisfactory'
    ]
}


# ───────────────────────────────────────────────────────────────────
def load_saved_assets() -> bool:
    """Return True if a saved model was found & loaded."""
    global model, tokenizer, index_label, maxlen
    try:
        model = load_model(MODEL_FILE)
        with open(TOKENIZER_PATH) as f:
            tokenizer = tokenizer_from_json(f.read())
        with open(LABELS_PATH) as f:
            meta = json.load(f)
        index_label = {i: l for l, i in meta["labels"].items()}
        maxlen = meta["maxlen"]
        return True
    except Exception:
        return False


# ───────────────────────────────────────────────────────────────────
def train_from_txt(txt_path: str) -> dict:
    """Train model on a `intent: sentence` text file and save assets."""
    global model, tokenizer, index_label, maxlen

    texts, labels = [], []
    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                lbl, txt = line.strip().split(":", 1)
                texts.append(txt.strip())
                labels.append(lbl.strip())
    if not texts:
        raise ValueError("No valid 'intent: sentence' lines found.")

    # label maps
    label_index = {l: i for i, l in enumerate(sorted(set(labels)))}
    index_label = {i: l for l, i in label_index.items()}
    y = np.array([label_index[l] for l in labels])

    # tokenizer & padded seqs
    tokenizer = Tokenizer(oov_token="<OOV>")
    tokenizer.fit_on_texts(texts)
    seqs = tokenizer.texts_to_sequences(texts)
    maxlen = max(len(s) for s in seqs)
    padded = pad_sequences(seqs, maxlen=maxlen, padding="post")

    # build & train model
    vocab_size, num_classes = len(tokenizer.word_index) + 1, len(label_index)
    model = Sequential(
        [
            Embedding(vocab_size, 16),
            GlobalAveragePooling1D(),
            Dense(16, activation="relu"),
            Dense(num_classes, activation="softmax"),
        ]
    )
    model.compile(
        loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"]
    )
    model.fit(padded, y, epochs=100, verbose=0)

    # save assets
    model.save(MODEL_FILE, overwrite=True)
    with open(TOKENIZER_PATH, "w") as f:
        f.write(tokenizer.to_json())
    with open(LABELS_PATH, "w") as f:
        json.dump({"labels": label_index, "maxlen": maxlen}, f)

    return {"num_intents": num_classes, "samples": len(texts), "maxlen": maxlen}


# ───────────────────────────────────────────────────────────────────
def predict_intent(text: str, threshold: float = 0.85) -> dict:
    
    if model is None or tokenizer is None:
        raise RuntimeError("Model not loaded. Train first or supply saved assets.")

    # text → integer sequence → padded array
    seq  = tokenizer.texts_to_sequences([text])
    pad  = pad_sequences(seq, maxlen=maxlen, padding="post")
    probs = model.predict(pad, verbose=0)[0]

    conf = float(np.max(probs))          # top soft‑max probability
    if conf >= threshold:
        intent = index_label[int(np.argmax(probs))]
    else:
        intent = "I could not understand"

    return {"intent": intent, "confidence": conf}

def analyze_conversation_intent(conversation_text: str) -> dict:
    """
    Analyze a full conversation transcript to extract intents, sentiment, and key topics.
    
    Args:
        conversation_text: Full conversation transcript text
        
    Returns:
        Dictionary containing:
        - primary_intent: Main intent of the conversation
        - all_intents: List of all detected intents with confidence
        - sentiment: Overall sentiment (positive/negative/neutral)
        - sentiment_score: Sentiment confidence score
        - key_topics: List of key topics discussed
        - urgency_level: High/Medium/Low based on keywords
        - customer_satisfaction: Estimated satisfaction level
        - action_items: Suggested actions based on conversation
    """
    try:
        # Clean and preprocess the conversation text
        cleaned_text = preprocess_conversation_text(conversation_text)
        
        # Extract user messages only (remove system messages)
        user_messages = extract_user_messages(conversation_text)
        full_text = ' '.join(user_messages)
        
        # Analyze primary intent
        primary_intent_result = predict_intent(full_text, threshold=0.7)
        primary_intent = primary_intent_result.get('intent', 'general_inquiry')
        primary_confidence = primary_intent_result.get('confidence', 0.0)
        
        # Analyze all intents from the conversation
        all_intents = analyze_multiple_intents(user_messages)
        
        # Analyze sentiment
        sentiment_result = analyze_sentiment(full_text)
        
        # Extract key topics
        key_topics = extract_key_topics(full_text)
        
        # Determine urgency level
        urgency_level = determine_urgency_level(full_text)
        
        # Estimate customer satisfaction
        customer_satisfaction = estimate_customer_satisfaction(sentiment_result, full_text)
        
        # Generate action items
        action_items = generate_action_items(primary_intent, sentiment_result, urgency_level)
        
        # Calculate conversation metrics
        conversation_metrics = calculate_conversation_metrics(conversation_text, user_messages)
        
        return {
            'primary_intent': primary_intent,
            'primary_confidence': primary_confidence,
            'all_intents': all_intents,
            'sentiment': sentiment_result['sentiment'],
            'sentiment_score': sentiment_result['score'],
            'key_topics': key_topics,
            'urgency_level': urgency_level,
            'customer_satisfaction': customer_satisfaction,
            'action_items': action_items,
            'conversation_metrics': conversation_metrics,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'error': f'Intent analysis failed: {str(e)}',
            'primary_intent': 'general_inquiry',
            'primary_confidence': 0.0,
            'all_intents': [],
            'sentiment': 'neutral',
            'sentiment_score': 0.0,
            'key_topics': [],
            'urgency_level': 'low',
            'customer_satisfaction': 'neutral',
            'action_items': [],
            'conversation_metrics': {},
            'analysis_timestamp': datetime.now().isoformat()
        }

def preprocess_conversation_text(text: str) -> str:
    """Clean and preprocess conversation text"""
    # Remove timestamps and speaker labels
    text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text)
    text = re.sub(r'^(SYSTEM|USER):\s*', '', text, flags=re.MULTILINE)
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    text = text.strip().lower()
    
    return text

def extract_user_messages(conversation_text: str) -> list:
    """Extract only user messages from conversation"""
    user_messages = []
    lines = conversation_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and 'USER:' in line.upper():
            # Extract message after USER: label
            message = line.split(':', 1)[1].strip() if ':' in line else line
            if message and message != '[No speech detected]':
                user_messages.append(message)
    
    return user_messages

def analyze_multiple_intents(messages: list) -> list:
    """Analyze multiple intents from conversation messages"""
    intents = []
    
    for message in messages:
        try:
            result = predict_intent(message, threshold=0.6)
            if result['intent'] != 'I could not understand':
                intents.append({
                    'intent': result['intent'],
                    'confidence': result['confidence'],
                    'message': message[:100] + '...' if len(message) > 100 else message
                })
        except Exception:
            continue
    
    # Group and aggregate intents
    intent_counts = Counter([intent['intent'] for intent in intents])
    aggregated_intents = []
    
    for intent_name, count in intent_counts.most_common():
        # Calculate average confidence for this intent
        confidences = [i['confidence'] for i in intents if i['intent'] == intent_name]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        aggregated_intents.append({
            'intent': intent_name,
            'confidence': avg_confidence,
            'frequency': count,
            'messages': [i['message'] for i in intents if i['intent'] == intent_name]
        })
    
    return aggregated_intents

def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of the conversation"""
    text_lower = text.lower()
    words = text_lower.split()
    
    positive_count = sum(1 for word in words if word in SENTIMENT_KEYWORDS['positive'])
    negative_count = sum(1 for word in words if word in SENTIMENT_KEYWORDS['negative'])
    neutral_count = sum(1 for word in words if word in SENTIMENT_KEYWORDS['neutral'])
    
    total_sentiment_words = positive_count + negative_count + neutral_count
    
    if total_sentiment_words == 0:
        return {'sentiment': 'neutral', 'score': 0.0}
    
    # Calculate sentiment score (-1 to 1)
    sentiment_score = (positive_count - negative_count) / total_sentiment_words
    
    # Determine sentiment category
    if sentiment_score > 0.1:
        sentiment = 'positive'
    elif sentiment_score < -0.1:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    return {
        'sentiment': sentiment,
        'score': sentiment_score,
        'positive_words': positive_count,
        'negative_words': negative_count,
        'neutral_words': neutral_count
    }

def extract_key_topics(text: str) -> list:
    """Extract key topics from the conversation"""
    topics = []
    text_lower = text.lower()
    
    # Check for each intent category
    for category, keywords in INTENT_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                topics.append({
                    'topic': category.replace('_', ' ').title(),
                    'keyword': keyword,
                    'category': category
                })
                break  # Only add each category once
    
    # Add common business topics
    business_keywords = {
        'pricing': ['price', 'cost', 'expensive', 'cheap', 'discount', 'promotion'],
        'quality': ['quality', 'good', 'bad', 'excellent', 'poor', 'satisfied'],
        'service': ['service', 'support', 'help', 'assistance', 'customer'],
        'delivery': ['delivery', 'shipping', 'arrive', 'receive', 'track'],
        'payment': ['payment', 'pay', 'credit card', 'invoice', 'bill']
    }
    
    for topic, keywords in business_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                topics.append({
                    'topic': topic.title(),
                    'keyword': keyword,
                    'category': 'business'
                })
                break
    
    return topics

def determine_urgency_level(text: str) -> str:
    """Determine urgency level based on keywords"""
    urgency_keywords = {
        'high': ['urgent', 'emergency', 'immediately', 'asap', 'critical', 'broken', 'not working'],
        'medium': ['soon', 'quickly', 'important', 'issue', 'problem', 'concern'],
        'low': ['when convenient', 'no rush', 'sometime', 'later', 'general']
    }
    
    text_lower = text.lower()
    
    for level, keywords in urgency_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return level
    
    return 'low'

def estimate_customer_satisfaction(sentiment_result: dict, text: str) -> str:
    """Estimate customer satisfaction level"""
    sentiment_score = sentiment_result['score']
    
    # Additional satisfaction indicators
    satisfaction_indicators = {
        'very_satisfied': ['love', 'amazing', 'excellent', 'perfect', 'fantastic'],
        'satisfied': ['good', 'great', 'happy', 'pleased', 'satisfied'],
        'neutral': ['okay', 'fine', 'alright', 'normal'],
        'dissatisfied': ['bad', 'poor', 'disappointed', 'unhappy'],
        'very_dissatisfied': ['terrible', 'awful', 'horrible', 'hate', 'angry']
    }
    
    text_lower = text.lower()
    
    for level, keywords in satisfaction_indicators.items():
        if any(keyword in text_lower for keyword in keywords):
            return level.replace('_', ' ')
    
    # Fall back to sentiment-based estimation
    if sentiment_score > 0.3:
        return 'satisfied'
    elif sentiment_score < -0.3:
        return 'dissatisfied'
    else:
        return 'neutral'

def generate_action_items(primary_intent: str, sentiment_result: dict, urgency_level: str) -> list:
    """Generate suggested action items based on conversation analysis"""
    action_items = []
    
    # Intent-based actions
    intent_actions = {
        'customer_service': ['Route to human agent', 'Escalate to supervisor'],
        'order_management': ['Check order status', 'Process refund if needed', 'Update order details'],
        'product_inquiry': ['Provide product information', 'Check inventory', 'Send catalog'],
        'technical_support': ['Create support ticket', 'Schedule technician visit', 'Provide troubleshooting steps'],
        'account_management': ['Reset password', 'Update account information', 'Verify account status'],
        'complaint': ['Apologize for inconvenience', 'Investigate issue', 'Offer compensation'],
        'general_inquiry': ['Provide information', 'Direct to appropriate department']
    }
    
    if primary_intent in intent_actions:
        action_items.extend(intent_actions[primary_intent])
    
    # Sentiment-based actions
    if sentiment_result['sentiment'] == 'negative':
        action_items.append('Follow up with customer')
        action_items.append('Offer apology and resolution')
    
    # Urgency-based actions
    if urgency_level == 'high':
        action_items.append('Prioritize response')
        action_items.append('Escalate immediately')
    
    return list(set(action_items))  # Remove duplicates

def calculate_conversation_metrics(conversation_text: str, user_messages: list) -> dict:
    """Calculate various conversation metrics"""
    total_lines = len(conversation_text.split('\n'))
    user_message_count = len(user_messages)
    system_message_count = conversation_text.upper().count('SYSTEM:')
    
    # Calculate average message length
    avg_message_length = 0
    if user_messages:
        total_length = sum(len(msg) for msg in user_messages)
        avg_message_length = total_length / len(user_messages)
    
    # Estimate conversation duration (rough estimate: 2-3 seconds per message)
    estimated_duration = user_message_count * 2.5
    
    return {
        'total_messages': user_message_count + system_message_count,
        'user_messages': user_message_count,
        'system_messages': system_message_count,
        'avg_message_length': round(avg_message_length, 1),
        'estimated_duration_seconds': round(estimated_duration, 1),
        'conversation_complexity': 'high' if user_message_count > 5 else 'medium' if user_message_count > 2 else 'low'
    }