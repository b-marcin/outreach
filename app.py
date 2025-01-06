import streamlit as st
import openai
import re
from typing import Dict, List, Tuple
import json
from datetime import datetime

def init_openai():
    if 'OPENAI_API_KEY' not in st.secrets:
        st.error('OpenAI API key not found. Please add it to your secrets.')
        st.stop()
    return openai.OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

def extract_profile_sections(profile_text: str) -> Dict[str, List[str]]:
    sections = {
        'experience': [],
        'education': [],
        'skills': [],
        'summary': '',
        'achievements': [],
        'certifications': []
    }
    
    lines = profile_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in ['experience', 'work history']) and len(line) < 30:
            current_section = 'experience'
            continue
        elif 'education' in lower_line and len(line) < 30:
            current_section = 'education'
            continue
        elif any(keyword in lower_line for keyword in ['skills', 'expertise', 'technologies']) and len(line) < 30:
            current_section = 'skills'
            continue
        elif any(keyword in lower_line for keyword in ['summary', 'about', 'overview']) and len(line) < 30:
            current_section = 'summary'
            continue
        elif any(keyword in lower_line for keyword in ['achievement', 'accomplishment', 'award']) and len(line) < 30:
            current_section = 'achievements'
            continue
        elif any(keyword in lower_line for keyword in ['certification', 'license', 'qualification']) and len(line) < 30:
            current_section = 'certifications'
            continue
            
        if current_section:
            if current_section == 'summary':
                sections[current_section] += line + ' '
            else:
                sections[current_section].append(line)
    
    return sections

def analyze_experience_relevance(experience: List[str], target_position: str, client: openai.OpenAI) -> List[Dict]:
    """Analyze the relevance of each experience entry to the target position."""
    try:
        analysis_prompt = f"""Analyze the following experience items for relevance to a {target_position} position.
        For each experience item, provide a relevance score (0-100) and key matching points.
        Experience items: {json.dumps(experience[:3])}"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert technical recruiter analyzing candidate experience."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.7
        )
        
        # Parse the response into structured data
        analysis = json.loads(response.choices[0].message.content)
        return analysis
    except:
        return [{"relevance": 50, "matching_points": ["Unable to analyze experience"]}]

def extract_key_achievements(sections: Dict[str, List[str]]) -> List[str]:
    """Extract key achievements and metrics from experience and achievements sections."""
    achievements = []
    
    # Look for metrics and achievements in experience
    for exp in sections['experience']:
        if any(keyword in exp.lower() for keyword in ['increased', 'decreased', 'improved', 'led', 'managed', 'created', '%', 'million', 'thousand']):
            achievements.append(exp)
    
    # Add explicit achievements
    achievements.extend(sections['achievements'])
    
    return achievements[:3]  # Return top 3 achievements

def generate_ai_message(client: openai.OpenAI, 
                       profile_sections: Dict[str, List[str]], 
                       target_position: str,
                       company_highlights: str,
                       tone: str,
                       message_length: str) -> str:
    """Generate a highly personalized outreach message using OpenAI's API."""
    
    # Analyze experience relevance
    experience_analysis = analyze_experience_relevance(
        profile_sections['experience'], 
        target_position,
        client
    )
    
    # Extract achievements
    key_achievements = extract_key_achievements(profile_sections)
    
    # Create enriched profile summary
    profile_summary = {
        "current_role": profile_sections['experience'][0] if profile_sections['experience'] else "Not specified",
        "key_skills": profile_sections['skills'][:5] if profile_sections['skills'] else [],
        "experience_highlights": experience_analysis,
        "key_achievements": key_achievements,
        "education": profile_sections['education'][:2] if profile_sections['education'] else [],
        "certifications": profile_sections['certifications']
    }
    
    length_guides = {
        "brief": "Keep the message concise, around 3-4 sentences.",
        "standard": "Write a standard-length message of about 5-6 sentences.",
        "detailed": "Create a comprehensive message with 7-8 sentences."
    }

    prompt = f"""As a technical recruiter, write a highly personalized LinkedIn outreach message for a {target_position} position.

Profile Information:
{json.dumps(profile_summary, indent=2)}

Company Information:
{company_highlights}

Requirements:
1. Tone: {tone}
2. Length: {length_guides[message_length]}
3. Must include:
   - Specific reference to their most relevant experience
   - Mention of their key achievements
   - Clear value proposition about the opportunity
   - Compelling reason why their background makes them an excellent fit
4. Formatting:
   - Use short paragraphs for readability
   - Include a clear call to action
   - End with a professional signature
5. Style:
   - Be genuine and conversational
   - Avoid recruiting clichés
   - Show you've done your research
   - Create urgency without being pushy

Format the message ready to send, starting with "Hi [Name]" and ending with a signature."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert technical recruiter known for writing highly engaging, personalized outreach messages that achieve exceptional response rates."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating message: {str(e)}")
        return None

# Initialize session state
if 'message_history' not in st.session_state:
    st.session_state.message_history = []

# Streamlit UI
st.title("Advanced AI Recruitment Message Generator")
st.write("Generate highly personalized outreach messages that get responses")

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
    
    with st.expander("💡 Writing Tips"):
        st.markdown("""
        **For Better Results:**
        - Include specific achievements and metrics
        - Add any certifications or special qualifications
        - Mention recent projects or technologies
        - Include team size and impact details
        """)
    
    st.markdown("---")
    st.markdown("### Recent Messages")
    for msg in st.session_state.message_history[-5:]:
        with st.expander(f"{msg['position']} - {msg['timestamp']:%H:%M}"):
            st.text_area("", msg['message'], height=100, key=f"history_{msg['timestamp']}")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    profile_text = st.text_area(
        "Paste LinkedIn Profile Content",
        height=300,
        help="Copy and paste the entire LinkedIn profile content here"
    )
    
    company_highlights = st.text_area(
        "Company/Role Highlights",
        height=100,
        help="Add key selling points about your company and the role",
        placeholder="E.g., Fast-growing startup, remote-first culture, cutting-edge tech stack..."
    )

with col2:
    target_position = st.text_input(
        "Target Position",
        help="Enter the position you're recruiting for"
    )
    
    st.markdown("### Profile Quality Check")
    if profile_text:
        sections = extract_profile_sections(profile_text)
        quality_score = sum([
            len(sections['experience']) > 0,
            len(sections['skills']) > 0,
            len(sections['education']) > 0,
            len(sections['summary']) > 0,
            len(sections['achievements']) > 0
        ]) * 20
        
        st.progress(quality_score / 100)
        st.text(f"Profile Completeness: {quality_score}%")
        
        if quality_score < 60:
            st.warning("Add more profile details for better personalization")

# Generate button and output
if st.button("Generate Message") and profile_text and target_position:
    try:
        client = init_openai()
        profile_sections = extract_profile_sections(profile_text)
        
        with st.spinner("Analyzing profile and generating personalized message..."):
            message = generate_ai_message(
                client,
                profile_sections,
                target_position,
                company_highlights,
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
            
            # Show analysis
            with st.expander("View Profile Analysis"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Key Skills Identified:**")
                    for skill in profile_sections['skills'][:5]:
                        st.markdown(f"- {skill}")
                
                with col2:
                    st.markdown("**Experience Highlights:**")
                    for exp in profile_sections['experience'][:3]:
                        st.markdown(f"- {exp}")

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
    
    3. Create a `.streamlit/secrets.toml` file:
       ```toml
       OPENAI_API_KEY = "your-api-key-here"
       ```
    
    4. Run the app:
       ```bash
       streamlit run app.py
       ```
    """)