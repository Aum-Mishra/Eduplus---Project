# Rasa Chatbot: How It Works, Purpose & Integration Guide

## 📋 Table of Contents
1. [What is This Chatbot?](#what-is-this-chatbot)
2. [Purpose & Use Cases](#purpose--use-cases)
3. [How It Works (System Architecture)](#how-it-works-system-architecture)
4. [Key Components Explained](#key-components-explained)
5. [Data Flow & Conversation Process](#data-flow--conversation-process)
6. [Integration with Other Systems](#integration-with-other-systems)
7. [Real-World Examples](#real-world-examples)
8. [Technical Details](#technical-details)
9. [Quick Start for Developers](#quick-start-for-developers)

---

## What is This Chatbot?

### Overview
This is a **Rasa-based conversational AI chatbot** designed for campus placement and recruitment guidance. It's an intelligent system that understands natural language and provides personalized placement predictions using machine learning.

### In Simple Terms
Imagine chatting with a smart assistant that:
- Answers questions about job placements
- Predicts your placement success probability
- Provides personalized company recommendations
- Understands casual conversation and typos
- Learns from conversations

---

## Purpose & Use Cases

### Primary Purpose
**Help students understand their campus placement prospects** by providing:
- Placement probability predictions
- Personalized company matching
- Interview preparation recommendations
- Career guidance

### Key Features

#### 1. **Conversational AI**
- Understands natural language
- Handles multiple conversation topics
- Remembers context in conversations
- Learns from interactions

#### 2. **Placement Prediction**
- Analyzes student profile (CGPA, skills, experience)
- Predicts probability of placement
- Shows company-specific success rates
- Provides improvement recommendations

#### 3. **Company Matching**
- Recommends suitable companies
- Matches skills with job requirements
- Filters by difficulty level (easy, medium, hard)
- Suggests interview types needed

#### 4. **Interactive Learning**
- Adapts responses based on user history
- Provides personalized feedback
- Suggests next steps for improvement
- Tracks conversation history

### Real-World Use Cases

```
Use Case 1: Student Checking Placement Prospects
────────────────────────────────────────────────
User: "Will I get placed?"
Bot: "Based on your profile, you have 78% placement probability"
User: "Which companies should I target?"
Bot: "You match 15 companies - 5 easy, 7 medium, 3 hard"

Use Case 2: Getting Interview Prep Help
────────────────────────────────────────
User: "What should I prepare for TCS?"
Bot: "TCS interviews focus on: aptitude, coding, HR"
User: "Can you test my aptitude?"
Bot: "Sure! Question 1: What is 25% of 480?"

Use Case 3: Career Guidance
────────────────────────────
User: "I'm weak in coding. What should I do?"
Bot: "Complete 50 LeetCode problems → DSA focus"
Bot: "Target service companies first (easier)")
Bot: "Practice 2 hours daily for 3 months"
```

---

## How It Works (System Architecture)

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Browser)                            │
│                    React Web Interface                           │
│                   (UI Eduplus Project)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP Requests
                         │ (Chat messages)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RASA CHATBOT SERVER                           │
│                    (Chatbot Folder)                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ NLU (Natural Language Understanding)                        │ │
│  │ - Recognizes user intent from text                          │ │
│  │ - Extracts entities (dates, numbers, names)                 │ │
│  │ - Matches to known patterns                                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Dialogue Management (Core Logic)                            │ │
│  │ - Maintains conversation flow                               │ │
│  │ - Decides what action to take                               │ │
│  │ - Follows conversation rules                                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Custom Actions (Business Logic)                             │ │
│  │ - Calls Backend API for predictions                         │ │
│  │ - Fetches company data                                      │ │
│  │ - Processes ML models                                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP Requests
                         │ (Get predictions, company data)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND API SERVER                             │
│            (Placement Integration Project)                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ /api/predict                    (Main prediction engine)    │ │
│  │ /api/companies                  (Company database)          │ │
│  │ /api/student-profile            (Student data)              │ │
│  │ /api/interview-prep             (Interview guidance)        │ │
│  │ /api/recommendation             (Company recommendations)   │ │
│  │ /api/probability-details        (Detailed analysis)         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                          │                                        │
│                          ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ML Model & Data Processing                                  │ │
│  │ - Trained models (sklearn, XGBoost)                         │ │
│  │ - Student & company data                                    │ │
│  │ - Features: CGPA, skills, DSA, etc.                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Conversation Flow Diagram

```
User Input (e.g., "Will I get placed?")
         │
         ▼
┌─────────────────────┐
│ NLU Processing      │ ← Converts text to structured data
│ - Intent: predict   │   (intent, entities, confidence)
│ - Entities: none    │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Dialogue Manager    │ ← Determines next action based on:
│ - Current state     │   - Conversation history
│ - Rules/Stories     │   - Intent recognized
│ - Context           │   - Domain knowledge
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Custom Action       │ ← Executes business logic:
│ - Fetch student ID  │   - Calls backend API
│ - Call /api/predict │   - Processes results
│ - Format response   │   - Prepares chatbot message
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Generate Response   │ ← Uses templates to create natural message
│ "You have 78%       │
│  placement prob"    │
└─────────────────────┘
         │
         ▼
User sees response in browser
```

---

## Key Components Explained

### 1. **NLU (Natural Language Understanding)**
**What it does:** Understands what the user is saying

```
Input:  "Will I get placed?"
         ↓
NLU processes:
- Intent: PREDICT_PLACEMENT (what user wants)
- Entities: none (no specific data mentioned)
- Confidence: 0.98 (very confident)
         ↓
Output: {"intent": "predict", "confidence": 0.98, "entities": []}
```

**Training Data Location:** `Chatbot/data/nlu.yml`

### 2. **Dialogue Manager**
**What it does:** Decides what to do based on user intent

```
Decision Logic:
IF user_intent == "predict_placement"
   AND has_student_profile == true
THEN
   trigger_action("action_predict_placement")
ELSE IF user_intent == "predict_placement"
   AND has_student_profile == false
THEN
   ask_for("student_id")
```

**Conversation Stories:** `Chatbot/data/stories.yml`
**Rules:** `Chatbot/data/rules.yml`
**Configuration:** `Chatbot/config.yml`

### 3. **Custom Actions**
**What they do:** Execute business logic and call external systems

```python
# Example: Prediction Action
@action.register("action_predict_placement")
def predict_placement(tracker, dispatcher, domain):
    # Get student data
    student_id = tracker.get_slot("student_id")
    
    # Call backend API
    response = requests.get(
        f"http://localhost:5000/api/predict?id={student_id}"
    )
    
    # Get prediction result
    probability = response.json()["probability"]
    
    # Send to user
    dispatcher.utter_message(
        text=f"You have {probability}% placement probability"
    )
```

**Files:** `Chatbot/actions/actions.py`, `Chatbot/actions/actions_placement.py`

### 4. **Domain**
**What it is:** Defines all possible intents, entities, slots, and responses

```yaml
intents:
  - predict_placement      # What user can ask
  - get_company_list       # Another question type
  - get_interview_prep     # Another question type

entities:
  - student_id             # Data to extract
  - company_name

slots:
  student_id:              # Remember during conversation
    type: text
  placement_prob:
    type: float

responses:
  utter_placement_result:
    - text: "You have {prob}% placement probability"
```

**File:** `Chatbot/domain.yml`

### 5. **Training Data**
**What it includes:** Examples the chatbot learns from

```yaml
# NLU Training (in nlu.yml)
- intent: predict_placement
  examples: |
    - Will I get placed?
    - Can I get a job?
    - What are my chances?
    - Predict my placement

# Conversation Stories (in stories.yml)
- story: predict_placement_flow
  steps:
    - intent: predict_placement
    - action: action_predict_placement
    - slot_was_set:
      - placement_prob: 0.78
    - response: utter_placement_result
```

**Files:** `Chatbot/data/nlu.yml`, `Chatbot/data/stories.yml`

### 6. **Trained Model**
**What it is:** The AI that remembers patterns learned from training data

```
Training Process:
─────────────────
Raw data (nlu.yml)
    ↓
NLU vectorization (convert text to numbers)
    ↓
Train neural networks
    ↓
Dialogue policy training
    ↓
Trained model (saved in models/)
```

**Files:** `Chatbot/models/` (auto-generated)

---

## Data Flow & Conversation Process

### Step-by-Step: "Will I get placed?" Conversation

```
STEP 1: User types message
────────────────────────────
Input: "Will I get placed?"
Sent to: Rasa Server (via HTTP)

STEP 2: Rasa NLU Process
────────────────────────
Rasa receives: "Will I get placed?"
               ↓
NLU processes text:
- Recognizes intent: PREDICT_PLACEMENT
- Extracts entities: none
- Confidence: 0.98
               ↓
Output: {
  "intent": {"name": "predict_placement", "confidence": 0.98},
  "entities": [],
  "text": "Will I get placed?"
}

STEP 3: Dialogue Manager Decision
──────────────────────────────────
Input: Intent (predict_placement)
       Conversation history
       Domain knowledge
       Current context
               ↓
Decision: 
- Check if student_id is known
- If yes: Proceed to prediction
- If no: Ask for student_id first
               ↓
Decision: "Proceed with prediction (student_id known)"

STEP 4: Trigger Action
──────────────────────
Action: action_predict_placement
               ↓
Inside action:
1. Get student_id from slot: "200001"
2. Make HTTP request to backend:
   GET http://localhost:5000/api/predict?student_id=200001
3. Backend processes:
   - Loads student data
   - Extracts features (CGPA, skills, DSA score)
   - Runs ML model
   - Returns: {"probability": 78, "top_companies": [...]}
4. Format response for user
               ↓
Result: {
  "probability": 78,
  "message": "You have 78% placement probability",
  "companies": ["TCS", "Infosys", "Wipro"]
}

STEP 5: Send Response to User
──────────────────────────────
Rasa sends HTTP response:
{
  "response": "You have 78% placement probability",
  "confidence": 0.98,
  "metadata": {...}
}
               ↓
React UI receives response
               ↓
Display to user:
"You have 78% placement probability ✅"

Total Time: ~500ms
```

---

## Integration with Other Systems

### Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  RASA CHATBOT                           │
│  (Reusable, Independent Service)                        │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬───────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
  React  Mobile  Desktop Web  Slack  Teams Discord
   UI    App     App    Portal        Bot
```

### 5 Ways to Integrate Rasa Chatbot

#### Method 1: HTTP API (Recommended)
**Use when:** You have a web/mobile app or service

```
Your Application
    │
    ├─ POST http://localhost:5005/webhooks/rest/webhook
    │  Body: {"message": "Will I get placed?"}
    │
    ▼
Rasa Server
    │
    ├─ Processes message
    ├─ Calls backend API
    ├─ Generates response
    │
    ▼
Response:
{
  "success": true,
  "responses": [
    {"text": "You have 78% placement probability"}
  ],
  "confidence": 0.98
}
```

**Code Example:**
```python
import requests
import json

def chat_with_rasa(user_message):
    """Send message to Rasa and get response"""
    
    url = "http://localhost:5005/webhooks/rest/webhook"
    
    payload = {
        "sender": "user123",
        "message": user_message
    }
    
    response = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    result = response.json()
    return result[0]["text"] if result else "I didn't understand"

# Usage
response = chat_with_rasa("Will I get placed?")
print(response)  # Output: "You have 78% placement probability"
```

#### Method 2: Slack Bot Integration
**Use when:** You want Slack integration

```
Slack User types: "Will I get placed?"
         │
         ▼
Rasa Slack Connector
         │
         ├─ Receives: message, user_id, channel
         ├─ Processes with Rasa
         ├─ Gets response
         │
         ▼
Response sent back to Slack channel
```

**Setup:**
```yaml
# Add to credentials.yml
slack:
  slack_channel: "placement-bot"
  slack_token: "xoxb-YOUR-TOKEN"
```

#### Method 3: Telegram Bot Integration
**Use when:** You want Telegram integration

```
Telegram User
    │
    ├─ /start
    ├─ Will I get placed?
    │
    ▼
Rasa Telegram Connector
    │
    ├─ Receives message
    ├─ Processes
    ├─ Gets response
    │
    ▼
Send response in Telegram
```

#### Method 4: Direct Python Integration
**Use when:** You're building another Python system

```python
from rasa.nlu.components import EntitySynonymMapper
from rasa.core.agent import Agent

# Load trained Rasa model
agent = Agent.load("path/to/models")

# Get response
responses = agent.handle_text("Will I get placed?")

for response in responses:
    print(response.get("text"))
```

#### Method 5: Container/Docker Integration
**Use when:** You want to deploy Rasa independently

```yaml
version: '3.8'
services:
  rasa:
    image: rasa/rasa:3.6.13
    ports:
      - "5005:5005"
    volumes:
      - ./Chatbot:/app
    command: run --enable-api --cors "*"
  
  backend:
    image: your-backend:latest
    ports:
      - "5000:5000"
  
  frontend:
    image: your-frontend:latest
    ports:
      - "3000:3000"
```

---

## Real-World Examples

### Example 1: Adding to University Portal
```
University Portal
    │
    └─ Widget: "Ask our Placement Bot"
            │
            ├─ Iframe embedding Rasa
            ├─ Students can ask questions
            ├─ Bot calls backend API
            ├─ Shows placement information
            │
    Button "Get My Placement Info" triggers Rasa conversation
```

### Example 2: Mobile App Integration
```
Mobile App (Flutter/React Native)
    │
    ├─ Chat Screen
    │   └─ Text input → Send to Rasa
    │   └─ Receive response → Display
    │
    ├─ HTTP Request to Rasa:
    │   POST /webhooks/rest/webhook
    │   {"message": "Will I get placed?"}
    │
    ├─ Rasa processes:
    │   → Calls backend /api/predict
    │   → Gets ML prediction
    │   → Formats response
    │
    └─ Display in app: "You have 78% placement probability"
```

### Example 3: SMS Integration
```
Student texts: "Place me" to +1-XXX-XXXX

SMS Gateway
    │
    ├─ Converts to text format
    ├─ Sends to Rasa via HTTP
    ├─ Gets response
    │
    └─ Send back as SMS: "You have 78% placement probability"
```

### Example 4: Command Line Integration
```bash
# User runs command
$ python chat.py

# Program uses Rasa:
Your response: Will I get placed?
Bot: You have 78% placement probability
```

---

## Technical Details

### Rasa Installation & Setup

```bash
# 1. Create virtual environment
python -m venv venv_rasa
source venv_rasa/bin/activate  # On Windows: venv_rasa\Scripts\activate

# 2. Install Rasa
pip install rasa==3.6.13

# 3. Install SDK for custom actions
pip install rasa-sdk>=3.6.2

# 4. Initialize project
rasa init

# 5. Train model
rasa train

# 6. Run chatbot
rasa run -m models --enable-api --cors "*"

# 7. In another terminal, run action server
rasa run actions
```

### Directory Structure

```
Chatbot/
├── actions/
│   ├── actions.py                    # Main custom actions
│   ├── actions_placement.py           # Placement-specific actions
│   └── __init__.py
├── data/
│   ├── nlu.yml                       # NLU training data
│   ├── stories.yml                   # Conversation stories
│   ├── rules.yml                     # Conversation rules
│   └── company_placement_db.csv      # Company database
├── models/                           # Trained models (auto-generated)
├── config.yml                        # Rasa configuration
├── domain.yml                        # Domain definition
├── endpoints.yml                     # Endpoints configuration
├── credentials.yml                   # Integration credentials
├── requirements.txt                  # Python dependencies
└── venv_rasa/                        # Virtual environment
```

### Configuration Files Explained

**config.yml** - Core Rasa settings:
```yaml
language: en                          # Language
pipeline:
  - name: SpacyNLP                    # NLU pipeline components
  - name: SpacyTokenizer
  - name: SpacyFeaturizer
  - name: DIETClassifier             # Intent classifier
    epochs: 100
  - name: CRFEntityExtractor         # Entity extractor
  - name: EntitySynonymMapper

policies:                             # Dialogue policies
  - name: MemoryPolicy
  - name: TEDPolicy                   # Neural dialogue generator
    epochs: 100
```

**domain.yml** - Allowed intents, entities, responses:
```yaml
version: "3.0"

intents:
  - predict_placement
  - get_companies
  - get_interview_prep

entities:
  - student_id
  - company_name

slots:
  student_id:
    type: text
  placement_prob:
    type: float

responses:
  utter_placement_result:
    - text: "You have {prob}% chances"
```

**endpoints.yml** - External connections:
```yaml
action_endpoint:
  url: "http://localhost:5055/webhook"  # Actions server
nlu_fallback:
  nlu_threshold: 0.4                     # Fallback if confidence < 40%
  ambiguity_threshold: 0.1
```

### API Endpoints

```
POST /webhooks/rest/webhook
├─ Send: {"message": "user text", "sender": "user123"}
├─ Response: [{"text": "bot response"}]

GET /api/predict
├─ Query: ?student_id=200001
├─ Response: {"probability": 78, "companies": [...]}

GET /api/companies
├─ Query: ?difficulty=medium
├─ Response: [{"name": "TCS", "placement": 85, ...}]

GET /health
├─ Response: {"status": "ok"}
```

---

## Quick Start for Developers

### 5-Minute Setup

```bash
# 1. Navigate to Chatbot
cd Chatbot

# 2. Activate environment
venv_rasa\Scripts\activate

# 3. Train model (if needed)
rasa train

# 4. Start Rasa
rasa run -m models --enable-api --cors "*"

# 5. In new terminal, start actions
rasa run actions

# 6. Test in browser
# Open: http://localhost:5005/webhooks/rest/webhook (POST)
# Send: {"message": "Will I get placed?", "sender": "user1"}
```

### Test with Python

```python
import requests
import json

# Test endpoint
url = "http://localhost:5005/webhooks/rest/webhook"
message = "Will I get placed?"

payload = {"message": message, "sender": "test_user"}
response = requests.post(url, json=payload)

print(json.dumps(response.json(), indent=2))
# Output:
# [
#   {
#     "text": "You have 78% placement probability",
#     "timestamp": 1693472400
#   }
# ]
```

### Common Modifications

**Add New Intent:**
1. Add to `domain.yml`:
```yaml
intents:
  - new_intent_name
```

2. Add examples to `data/nlu.yml`:
```yaml
- intent: new_intent_name
  examples: |
    - example1
    - example2
```

3. Add story to `data/stories.yml`:
```yaml
- story: new_story
  steps:
    - intent: new_intent_name
    - action: action_name
```

4. Retrain:
```bash
rasa train
```

**Add Custom Action:**
1. Code in `actions/actions.py`:
```python
class ActionCustom(Action):
    def name(self) -> Text:
        return "action_custom"
    
    def run(self, tracker, dispatcher, domain):
        # Your logic here
        dispatcher.utter_message("Response")
        return []
```

2. Add to `domain.yml`:
```yaml
actions:
  - action_custom
```

3. Restart action server:
```bash
rasa run actions
```

---

## Summary

### What You Now Know

✅ **Purpose:** Conversational AI for placement guidance
✅ **How it works:** NLU → Dialogue Manager → Custom Actions → Response
✅ **Key components:** NLU, domain, training data, dialogue policies
✅ **Integration methods:** 5 ways (HTTP, Slack, Telegram, Python, Docker)
✅ **Architecture:** Frontend → Rasa → Backend API
✅ **Deployment:** Can run independently, call backend as needed

### Next Steps

1. **To Use:** Follow setup guide, run `rasa shell`
2. **To Extend:** Add intents/stories to train data, retrain
3. **To Integrate:** Use HTTP API method for other apps
4. **To Deploy:** Use Docker/Kubernetes for production
5. **To Customize:** Modify actions.py for your business logic

### Files to Know

- `config.yml` - Core settings
- `domain.yml` - Intents, entities, responses
- `nlu.yml` - Training examples
- `stories.yml` - Conversation flows
- `actions.py` - Business logic
- `endpoints.yml` - Connections

---

## Questions & Answers

**Q: Can I use Rasa with my existing system?**
A: YES! Use HTTP API integration method. Your app sends messages to Rasa, gets responses back.

**Q: Do I need to understand machine learning?**
A: NO! Rasa handles it. You provide training data, it learns automatically.

**Q: How long to train the model?**
A: ~30 seconds with current data. Scales up with more data.

**Q: Can I deploy to cloud?**
A: YES! Docker containerize it, deploy to AWS/GCP/Azure.

**Q: Where does the ML prediction come from?**
A: Backend API. Rasa calls it, backend returns prediction.

**Q: Is it secure?**
A: Add authentication to API endpoints. Use HTTPS in production.

**Q: How many conversations can it handle?**
A: Single Rasa instance: ~100 concurrent. Scale with load balancer for more.

**Q: Can I use it offline?**
A: YES! It's self-contained. Only needs internet if calling external APIs.

---

*This document explains the complete Rasa chatbot system, its purpose, how it works, and how to integrate it anywhere.*

