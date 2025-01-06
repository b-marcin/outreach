import streamlit as st
import openai
import re
from typing import Dict, List
import json
from datetime import datetime

def init_openai():
    """Initialize OpenAI client with API key from Streamlit secrets."""
    if 'OPENAI_API_KEY' not in st.secrets:
        st.error('OpenAI API key not found. Please add it to your secrets.')
        st.stop()
    return openai.OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

def extract_profile_sections(profile_text: str) -> Dict[str, List[str]]:
    """
    Extract key sections from a LinkedIn profile text.
    Returns a dictionary with sections like experience, skills, education.
    """
    sections = {
        'experience': [],
        'education': [],
        'skills': [],
        'summary': ''
    }
    
    lines = profile_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        lower_line = line.lower()
        if 'experience' in lower_line and len(line) < 30:
            current_section = 'experience'
            continue
        elif 'education' in lower_line and len(line) < 30:
            current_section = 'education'
            continue
        elif 'skills' in lower_line and len(line) < 30:
            current_section = 'skills'
            continue
        elif 'summary' in lower_line and len(line) < 30:
            current_section = 'summary'
            continue
            
        if current_section:
            if current_section == 'summary':
                sections[current_section] += line + ' '
            else:
                sections[current_section].append(line)
    
    return sections

def generate_ai_message(client: openai.OpenAI, 
                       profile_sections: Dict[str, List[str]], 
                       target_position: str,
                       tone: str,
                       message_length: str) -> str:
    """
    Generate a personalized outreach message using OpenAI's API.
    """
    # Create a structured profile summary
    profile_summary = {
        "current_role": profile_sections['experience'][0] if profile_sections['experience'] else "Not specified",
        "key_skills": profile_sections['skills'][:5] if profile_sections['skills'] else [],
        "experience_highlights": profile_sections['experience'][:3] if profile_sections['experience'] else [],
        "education": profile_sections['education'][:2] if profile_sections['education'] else []
    }
    
    # Define length parameters
    length_guides = {
        "brief": "Keep the message concise, around 2-3 sentences.",
        "standard": "Write a standard-length message of about 4-5 sentences.",
        "detailed": "Create a comprehensive message with 6-7 sentences."
    }

    # Construct the prompt
    prompt = f"""As a technical recruiter, write a personalized LinkedIn outreach message for a {target_position} position.

Profile Information:
{json.dumps(profile_summary, indent=2)}

Requirements:
1. Tone: {tone}
2. Length: {length_guides[message_length]}
3. Must mention specific aspects of their background that make them a good fit
4. Include a clear call to action
5. Keep it professional but conversational
6. Don't use cliche recruiting phrases
7. Make specific references to their experience and skills

Format the message ready to send, starting with "Hi [Name]" and ending with a signature."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an experienced technical recruiter who writes personalized, engaging outreach messages."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating message: {str(e)}")
        return None

# Initialize session state for message history
if 'message_history' not in st.session_state:
    st.session_state.message_history = []

# Streamlit UI
st.title("AI-Powered LinkedIn Outreach Generator")
st.write("Generate personalized recruitment messages using AI")

# Settings and input section
with st.sidebar:
    st.header("Message Settings")
    tone = st.select_slider(
        "Message Tone",
        options=["Professional", "Friendly", "Casual"],
        value="Professional"
    )
    
    message_length = st.select_slider(
        "Message Length",
        options=["brief", "standard", "detailed"],
        value="standard"
    )
    
    st.markdown("---")
    st.markdown("### Message History")
    for msg in st.session_state.message_history[-5:]:
        st.text(f"{msg['timestamp']:%H:%M:%S}")
        st.text_area("", msg['message'], height=100, key=f"history_{msg['timestamp']}")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    profile_text = st.text_area(
        "Paste LinkedIn Profile Content",
        height=300,
        help="Copy and paste the entire LinkedIn profile content here"
    )

with col2:
    target_position = st.text_input(
        "Target Position",
        help="Enter the position you're recruiting for"
    )
    
    st.markdown("### Tips for best results:")
    st.markdown("""
    - Include the full profile text
    - Ensure experience and skills sections are included
    - More detail leads to better personalization
    """)

# Generate button and output
if st.button("Generate Message") and profile_text and target_position:
    try:
        client = init_openai()
        profile_sections = extract_profile_sections(profile_text)
        
        with st.spinner("Generating personalized message..."):
            message = generate_ai_message(
                client,
                profile_sections,
                target_position,
                tone,
                message_length
            )
        
        if message:
            st.markdown("### Generated Message:")
            st.text_area("", message, height=300)
            
            # Save to history
            st.session_state.message_history.append({
                'timestamp': datetime.now(),
                'message': message,
                'position': target_position
            })
            
            # Show extracted sections for verification
            with st.expander("View Extracted Profile Sections"):
                for section, content in profile_sections.items():
                    st.markdown(f"**{section.title()}:**")
                    if isinstance(content, list):
                        for item in content:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown(content)

# Setup instructions
st.markdown("---")
with st.expander("Installation & Usage Instructions"):
    st.markdown("""
    To run this app locally:
    
    1. Save this code in a file named `app.py`
    
    2. Install required packages:
       ```bash
       pip install streamlit openai
       ```
    
    3. Create a `.streamlit/secrets.toml` file in your project directory:
       ```toml
       OPENAI_API_KEY = "your-api-key-here"
       ```
    
    4. Run the app:
       ```bash
       streamlit run app.py
       ```
    
    5. The app will open in your default web browser
    """)