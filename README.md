# **AI Mediation Assistant**

An innovative peer mediation application leveraging Gemma LLM to resolve interpersonal conflicts through AI-driven dialogue. Built for the **Gemma Lablab Hackathon**, this project demonstrates how AI can foster constructive communication and conflict resolution in real-time.

---

## **Overview**

The AI Mediation Assistant facilitates structured conversations between two parties in conflict. With Gemma LLM as the mediator, the application ensures both parties are heard, acknowledged, and guided toward resolution in a neutral, supportive environment.

---

## **Features**
- 🎭 **Role-Specific Responses**:
  - Understands and addresses each party’s unique perspective (e.g., Concern Raiser vs. Responder).
- 🔄 **Dynamic Context Awareness**:
  - Tracks participants, their concerns, and maintains conversation flow.
- 💬 **Custom Messaging UI**:
  - User-friendly chat interface for seamless communication.
- 🔍 **Real-Time Logging**:
  - Logs conversations and tracks mediation progress for review and transparency.
- 🔗 **Firebase Integration**:
  - Persistent storage of mediation cases and sessions using Firestore.
- 🤖 **Powered by Gemma LLM**:
  - Contextually-aware, AI-driven mediator capable of understanding emotions and fostering constructive dialogue.

---

## **How It Works**

1. **Mediation Case Creation**:
   - Users initiate a mediation session by identifying themselves and the other party.
   - Each participant receives a unique session code to join the mediation.

2. **Structured Conversation Flow**:
   - **Party 1**: Raises the concern and describes the issue.
   - **Party 2**: Responds to the concern and shares their perspective.
   - **Mediator**: Guides the conversation with empathetic and constructive prompts.

3. **Conflict Resolution**:
   - Through guided dialogue, parties gain clarity and work toward a resolution.

---

## **Tech Stack**
- **Frontend**: [Streamlit](https://streamlit.io) for a lightweight, interactive interface.
- **Backend**:
  - [Gemma LLM](https://lablab.ai/) for AI-driven mediation responses.
  - [Firebase](https://firebase.google.com/) for real-time database and session management.
- **Programming Language**: Python
- **API**: Gemma LLM API for generating responses.

---

## **Setup Instructions**

### Prerequisites
- Python 3.8+
- Firebase Project with Firestore enabled.
- Gemma LLM API Key.

### Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/ai-mediation-assistant.git
   cd ai-mediation-assistant
