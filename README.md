# Twilio Voice AI Assistant
A comprehensive voice AI system built with Twilio, Python, and TensorFlow that provides intelligent customer service with automatic call forwarding to human agents.

## 🎯 Project Overview

This project creates an intelligent voice AI assistant that can:
- **Understand customer intent** using machine learning
- **Handle customer inquiries** automatically
- **Forward calls to human agents** when needed
- **Record and transcribe** all conversations
- **Provide personalized responses** based on customer needs

## 🚀 Key Features

### 🤖 AI-Powered Voice Assistant
- **Intent Recognition**: Uses TensorFlow/Keras model to understand customer intent
- **Natural Language Processing**: Processes speech input and generates contextual responses
- **Conversation Flow**: Maintains context throughout the conversation
- **Multi-turn Dialogues**: Handles complex customer interactions

### 📞 Call Forwarding System
- **Automatic Detection**: Detects when customers want to speak with human agents
- **Smart Transfer**: Seamlessly forwards calls to configured human agent numbers
- **Keyword Recognition**: Identifies customer service requests using predefined keywords
- **Audit Logging**: Tracks all forwarding actions for monitoring

### 🎙️ Voice & Recording Features
- **Speech-to-Text**: Converts customer speech to text for processing
- **Call Recording**: Automatically records all conversations
- **Transcript Generation**: Creates detailed conversation logs
- **Audio Playback**: Web interface to review recordings

### 📊 Monitoring & Analytics
- **Conversation Logs**: Detailed logs of all customer interactions
- **Call Analytics**: Track call duration, intent detection accuracy
- **Recording Management**: Organize and access call recordings
- **Performance Metrics**: Monitor AI model confidence and accuracy

## 🛠️ Technical Architecture

### Core Components
- **Flask Web Server**: Handles Twilio webhooks and voice processing
- **TensorFlow/Keras Model**: Intent classification and response generation
- **Twilio Voice API**: Call handling, speech recognition, and recording
- **Environment Configuration**: Secure credential management

### AI Model Features
- **Intent Classification**: Categorizes customer requests (orders, support, billing, etc.)
- **Confidence Scoring**: Provides confidence levels for AI responses
- **Context Awareness**: Maintains conversation context across turns
- **Fallback Handling**: Graceful handling of unclear requests

### Call Forwarding Logic
- **Keyword Detection**: Monitors for customer service requests
- **Transfer Triggers**: Automatic forwarding based on detected keywords
- **Agent Routing**: Directs calls to appropriate human agents
- **Logging System**: Comprehensive audit trail of all transfers

## 🚀 Getting Started

### Step 1: Clone the Repository
```bash
git clone <your-repository-url>
cd TwilioVoicePython
```

### Step 2: Set Up Python Environment
```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional packages if needed
pip install tensorflow flask twilio python-dotenv requests waitress
```

### Step 3: Environment Configuration
Create a `.env` file in the project root:
```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here

# Webhook Configuration
NGROK_URL=https://your-ngrok-url.ngrok.io

# Human Agent Configuration
HUMAN_AGENT_NUMBER=+1234567890

# Flask Configuration
SECRET_KEY=your_secret_key_here
```

### Step 4: Verify Model Files
Ensure these AI model files are present in the project root:
```bash
# Check if model files exist
ls intent_model.keras tokenizer.json labels.json
```

### Step 5: Set Up Ngrok (for webhook testing)
```bash
# Install ngrok (if not already installed)
# Download from https://ngrok.com/download

# Start ngrok to expose your local server
ngrok http 5000
```

### Step 6: Configure Twilio Webhook
1. Go to your Twilio Console
2. Navigate to Phone Numbers → Manage → Active numbers
3. Click on your phone number
4. Set the webhook URL for voice calls to: `https://your-ngrok-url.ngrok.io/voice`

### Step 7: Start the Application
```bash
# Option 1: Development mode (Flask built-in server)
python app.py

# Option 2: Production mode (Waitress server - recommended)
waitress-serve --port=5000 app:app

# Option 3: Using make_call.py for local testing
python make_call.py
```

### Step 8: Test the System
1. Call your Twilio phone number
2. Speak one of the sample questions
3. Test the call forwarding by saying "I want to speak with customer service"
4. Check the logs in the console and `transcripts/` directory

## 🏃‍♂️ Running the Project

### Development Mode
```bash
# Start Flask development server
python app.py
```
- Runs on `http://localhost:5000`
- Auto-reloads on code changes
- Debug mode enabled
- Best for development and testing

### Production Mode
```bash
# Install waitress (if not already installed)
pip install waitress

# Start production server
waitress-serve --port=5000 app:app
```
- Production-ready WSGI server
- Better performance and stability
- Recommended for production deployment
- Handles multiple concurrent requests

### Local Testing with make_call.py
```bash
# Run local call simulation
python make_call.py
```
- Simulates Twilio voice calls locally
- Tests the voice AI system without actual phone calls
- Useful for development and debugging
- No need for Twilio phone number during development

### Server Options Comparison

| Option | Use Case | Performance | Features |
|--------|----------|-------------|----------|
| `python app.py` | Development | Basic | Auto-reload, Debug mode |
| `waitress-serve` | Production | High | Stable, Concurrent |
| `python make_call.py` | Local Testing | N/A | No external calls needed |

## 📋 Setup Instructions

### 1. Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install additional packages
pip install tensorflow flask twilio python-dotenv requests
```

### 2. Environment Configuration
Create a `.env` file with your credentials:
```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here

# Webhook Configuration
NGROK_URL=https://your-ngrok-url.ngrok.io

# Human Agent Configuration
HUMAN_AGENT_NUMBER=+1234567890

# Flask Configuration
SECRET_KEY=your_secret_key_here
```

### 3. Model Setup
```bash
# The AI model files should be present:
# - intent_model.keras (TensorFlow model)
# - tokenizer.json (Text tokenizer)
# - labels.json (Intent classification labels)
```

### 4. Start the Application
```bash
python app.py
```

## 🎮 Usage Examples

### Customer Service Scenarios

**Scenario 1: Order Inquiry**
```
Customer: "I want to check my order status"
AI: "I can help you with that. Please provide your order number."
```

**Scenario 2: Human Agent Request**
```
Customer: "I need to speak with customer service"
AI: "I understand you'd like to speak with a human agent. Please hold while I transfer your call."
[Call forwarded to human agent]
```

**Scenario 3: Billing Question**
```
Customer: "I have a question about my bill"
AI: "I can help you with billing questions. What specific information do you need?"
```

### Call Forwarding Keywords
The system automatically forwards calls when customers mention:
- "customer service"
- "human agent"
- "speak to someone"
- "representative"
- "operator"
- "live person"
- And many more...

## 📁 Project Structure

```
TwilioVoicePython/
├── app.py                 # Main Flask application
├── intent_core.py        # AI model loading and prediction
├── intent_model.keras    # Trained TensorFlow model
├── tokenizer.json        # Text tokenization data
├── labels.json          # Intent classification labels
├── requirements.txt     # Python dependencies
├── recordings/         # Call recording storage
├── transcripts/        # Conversation logs
└── .env               # Environment configuration
```

## 🔧 Configuration Options

### Customizing Call Forwarding
Edit the `CUSTOMER_SERVICE_KEYWORDS` list in `app.py`:
```python
CUSTOMER_SERVICE_KEYWORDS = [
    "customer service", "customer support", "human agent", "agent",
    # Add your custom keywords here
]
```

### Modifying AI Responses
Update the intent responses in the `predict_intent` function in `intent_core.py`.

### Changing Transfer Messages
Modify the `forward_to_human_agent` function in `app.py`.

## 📊 Monitoring & Logs

### Conversation Logs
- Location: `transcripts/` directory
- Format: Text files with timestamps
- Content: Full conversation transcripts

### Call Recordings
- Location: `recordings/` directory
- Format: MP3 files
- Access: Web interface at `/play/<recording_sid>`

### System Logs
- Console output with detailed logging
- Error tracking and debugging information
- Performance metrics and timing data

## 🚀 Deployment

### Local Development
```bash
# Development server
python app.py

# Or production server for local testing
waitress-serve --port=5000 app:app
```

### Production Deployment
1. Install production dependencies:
   ```bash
   pip install waitress
   ```
2. Set up environment variables in production
3. Configure SSL certificates
4. Configure Twilio webhook URLs
5. Start with production server:
   ```bash
   waitress-serve --port=5000 app:app
   ```

### Ngrok for Testing
```bash
ngrok http 5000
```
Update your Twilio webhook URL with the ngrok URL.

## 🔒 Security Features

- **Environment Variables**: Secure credential management
- **HTTPS Only**: Secure cookie configuration
- **Input Validation**: Sanitized speech input processing
- **Audit Logging**: Comprehensive activity tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the logs in `transcripts/` directory
- Review console output for error messages
- Verify environment variable configuration
- Test with sample conversations

## 📈 Future Enhancements

- **Multi-language Support**: Add support for multiple languages
- **Advanced Analytics**: Detailed call analytics and reporting
- **CRM Integration**: Connect with customer relationship management systems
- **Voice Biometrics**: Speaker identification and authentication
- **Sentiment Analysis**: Customer mood and satisfaction tracking
