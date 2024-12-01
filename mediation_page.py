
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import time
import requests
import json
from enum import Enum
import time

def custom_message_box(content, is_user=False):
    if is_user:
        st.markdown(f"""
        <div style="
            display: inline-block;
            background-color: #007AFF;
            color: white;
            padding: 6px 10px;
            border-radius: 12px 12px 4px 12px;
            margin: 2px 0;
            margin-left: auto;
            margin-right: 5%;
            max-width: 70%;
            white-space: pre-wrap;
            word-wrap: break-word;
            float: right;
            clear: both;
            line-height: 1.2;
            font-size: 0.95em;
        ">
        {content}
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="
            display: inline-block;
            background-color: #E9ECEF;
            color: black;
            padding: 6px 10px;
            border-radius: 12px 12px 12px 4px;
            margin: 2px 0;
            margin-left: 5%;
            max-width: 70%;
            white-space: pre-wrap;
            word-wrap: break-word;
            float: left;
            clear: both;
            line-height: 1.2;
            font-size: 0.95em;
        ">
        🤖 {content}
        """, unsafe_allow_html=True)
        
# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()



class MediationStep(Enum):
    PARTY1_INITIAL = "party1_initial"
    PARTY2_INITIAL = "party2_initial"
    DISCUSSION = "discussion"

class MediatorAPI:
    def __init__(self):
        
        self.api_key = "placeholder"
        self.base_url = "https://api.aimlapi.com/chat/completions"
        self.model = "google/gemma-2-27b-it"
    
    def generate_response(self, message, is_first_party, names=None):
        """Generate response with clear role assignments"""
        try:
            # Use predefined names for context
            if not is_first_party:
                role_context = f"You are speaking with {names['party2']}, who was mentioned in the concern."
            else:
                role_context = f"You are speaking with {names['party1']}, who raised the concern."
            
            system_prompt = f"""
            {role_context}
            Listen carefully and respond based on the roles:
            - For the concern raiser, acknowledge their concern and ask for more details.
            - For the responder, explain the concern and ask for their perspective.
            """
            
            formatted_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            response = requests.post(
                url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            )
            
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Mediator error: {str(e)}")
            raise

class MediationCase:
    def __init__(self, case_id):
        self.case_id = case_id
        self.db = firestore.client()
        self.mediator = MediatorAPI()
        self.names = {}  # Store names for context
    
    def create_case(self, party1_name, party2_name):
        """Create a new mediation case with two sessions and predefined names"""
        party1_session = f"{self.case_id}_party1"
        party2_session = f"{self.case_id}_party2"
        
        # Ensure names are stored properly
        self.db.collection('mediation_cases').document(self.case_id).set({
            'created_at': datetime.now(),
            'party1_session': party1_session,
            'party2_session': party2_session,
            'last_update': datetime.now(),
            'waiting_for': 'party2',
            'names': {
                'party1': party1_name,
                'party2': party2_name
            }
        })
        
        # Create session documents
        self.db.collection('mediation_sessions').document(party1_session).set({
            'created_at': datetime.now()
        })
        self.db.collection('mediation_sessions').document(party2_session).set({
            'created_at': datetime.now()
        })
        
        return party1_session, party2_session


    
    def get_case_status(self):
        """Get current status of the mediation case"""
        doc = self.db.collection('mediation_cases').document(self.case_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def get_messages(self, session_id):
        """Get all messages for a specific session"""
        messages = self.db.collection('mediation_sessions').document(session_id)\
            .collection('messages').order_by('timestamp').stream()
        return [msg.to_dict() for msg in messages]
    
    def add_message(self, session_id, user_id, content):
        """Add a message to a specific session"""
        self.db.collection('mediation_sessions').document(session_id)\
            .collection('messages').add({
                'user_id': user_id,
                'content': content,
                'timestamp': datetime.now()
            })
    
    def handle_message(self, session_id, user_id, message):
        """Handle message with explicit role validation"""
        case_status = self.get_case_status()
        if not case_status:
            raise ValueError("Mediation case not found!")
        
        # Ensure names field is available
        names = case_status.get('names')
        if not names or 'party1' not in names or 'party2' not in names:
            raise ValueError("Participant names are missing in the mediation case.")
        
        is_party1 = session_id.endswith("party1")
        other_session = case_status['party2_session'] if is_party1 else case_status['party1_session']
        
        # Process the message as usual
        self.add_message(session_id, user_id, message)
        mediator_response = self.mediator.generate_response(message, is_party1, names)
        self.add_message(other_session, 'mediator', mediator_response)
        
        # Update waiting state
        next_party = 'party2' if is_party1 else 'party1'
        self.db.collection('mediation_cases').document(self.case_id).update({
            'waiting_for': next_party,
            'last_update': datetime.now()
        })

    
    def _extract_names(self, message):
        """Extract names from initial message"""
        names = {}
        words = message.split()
        
        # Look for "I am" or "I'm"
        if "I am" in message or "I'm" in message:
            try:
                idx = words.index("am") if "am" in words else words.index("I'm")
                if idx + 1 < len(words):
                    names['party1'] = words[idx + 1].strip('.,!?')
            except ValueError:
                pass
        
        # Look for other name in message
        for word in words:
            word = word.strip('.,!?')
            if word not in names.values() and word[0].isupper() and len(word) > 1:
                names['party2'] = word
                break
        
        return names
    
def main():
    st.title("🤝 AI Mediation Assistant")
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{int(time.time())}"
    
    menu = st.sidebar.radio("Navigation", ["Start New Mediation", "Join Mediation"])
    
    if menu == "Start New Mediation":
        st.header("Start New Mediation")
        
        with st.form("new_mediation"):
            your_name = st.text_input("Who are you?")
            other_party_name = st.text_input("Who do you want to mediate with?")
            initial_statement = st.text_area("What would you like to discuss?")
            submitted = st.form_submit_button("Create Mediation Case")
            
            if submitted and your_name and other_party_name and initial_statement:
                case_id = f"case_{int(time.time())}"
                case = MediationCase(case_id)
                party1_session, party2_session = case.create_case(your_name, other_party_name)
                
                try:
                    # Set the initial message
                    case.handle_message(party1_session, st.session_state.user_id, initial_statement)
                    st.success("Mediation case created!")
                    st.info(f"""Share these codes with the participants:
                    \nYour Code (Party 1): {party1_session}
                    \nOther Party's Code: {party2_session}""")
                except Exception as e:
                    st.error(f"Error starting mediation: {str(e)}")
    
    elif menu == "Join Mediation":
        session_id = st.text_input("Enter your session code:")
        
        if session_id:
            try:
                case_id = "_".join(session_id.split("_")[:-1])
                party_number = session_id.split("_")[-1]
                case = MediationCase(case_id)
                case_status = case.get_case_status()
                
                if not case_status:
                    st.error("Invalid session code.")
                    return

                st.subheader("Your Private Mediation Session")
                
                # Show messages from this session only
                messages = case.get_messages(session_id)
                for msg in messages:
                    is_user = msg['user_id'] != 'mediator'
                    custom_message_box(msg['content'], is_user)

                can_respond = case_status['waiting_for'] == party_number
                
                with st.form("send_message"):
                    message = st.text_area(
                        "Your message:" if can_respond else 
                        "Waiting for the other party...",
                        disabled=not can_respond
                    )
                    submit_button = st.form_submit_button("Send", disabled=not can_respond)
                    
                    if submit_button and message and can_respond:
                        try:
                            case.handle_message(session_id, st.session_state.user_id, message)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error processing message: {str(e)}")

                # Status section at the bottom
                st.divider()
                col1, col2 = st.columns([3, 1])
                with col1:
                    if case_status['waiting_for'] == party_number:
                        st.success("🟢 Your turn to respond")
                    else:
                        st.warning("⏳ Waiting for other party...")
                with col2:
                    if case_status['waiting_for'] != party_number:
                        if st.button("Check for updates"):
                            st.rerun()
                
                # Add auto-refresh if waiting for response
                if not can_respond:
                    time.sleep(20)
                    st.rerun()
            
            except Exception as e:
                st.error(f"Error accessing session: {str(e)}")

                    
if __name__ == "__main__":
    main()