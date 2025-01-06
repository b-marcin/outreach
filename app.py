import streamlit as st
import requests
import re
from typing import Dict, List, Tuple
import json
from datetime import datetime

def init_huggingface():
    """Initialize Hugging Face with free API token."""
    try:
        if 'HF_API_KEY' not in st.secrets:
            # Using dummy key for demonstration - get yours from huggingface.co
            return "hf_dummy_key"
        return st.secrets['HF_API_KEY']
    except Exception as e:
        st.error(f'Failed to initialize Hugging Face client: {str(e)}')
        st.stop()

def query_free_model(prompt: str, api_key: str) -> str:
    """Query FLAN-T5 model using Hugging Face's free inference API."""
    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        return response.json()[0]['generated_text']
    except Exception as e:
        st.warning(f"Model query failed: {str(e)}")
        return "Error generating message. Please try again."

def extract_profile_sections(profile_text: str) -> Dict[str, List[str]]:
    """Extract and categorize sections from LinkedIn profile text."""
    sections = {
        'experience': [],
        'education': [],
        'skills': [],
        'summary': '',
        'achievements': [],
        'certifications': []
    }
    
    try:
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
            elif any(keyword in lower_line for keyword in ['skills', 'expertise']) and len(line) < 30:
                current_section = 'skills'
                continue
            elif any(keyword in lower_line for keyword in ['summary', 'about']) and len(line) < 30:
                current_section = 'summary'
                continue
            elif any(keyword in lower_line for keyword in ['achievement', 'accomplishment']) and len(line) < 30:
                current_section = 'achievements'
                continue
            elif any(keyword in lower_line for keyword in ['certification', 'license']) and len(line) < 30:
                current_section = 'certifications'
                continue
                
            if current_section:
                if current_section == 'summary':
                    sections[current_section] += line + ' '
                else:
                    sections[current_section].append(line)
        
        return sections
    except Exception as e:
        st.error(f"Error extracting profile sections: {str(e)}")
        return sections

def analyze_experience(experience: List[str], target_position: str) -> List[Dict]:
    """Analyze experience locally without API calls."""
    relevant_keywords = {
        'developer': ['coding', 'programming', 'software', 'development', 'engineering'],
        'manager': ['lead', 'managing', 'leadership', 'team', 'strategy'],
        'analyst': ['analysis', 'data', 'research', 'reporting', 'metrics'],
        # Add more role-specific keywords
    }
    
    results = []
    position_type = next((k for k in relevant_keywords.keys() if k in target_position.lower()), 'general')
    keywords = relevant_keywords.get(position_type, [])
    
    for exp in experience[:3]:  # Analyze top 3 experiences
        relevance = sum(1 for keyword in keywords if keyword in exp.lower()) * 20
        matching_points = [
            point for point in exp.split('. ')
            if any(keyword in point.lower() for keyword in keywords)
        ]
        results.append({
            'relevance': min(relevance + 40, 100),  # Base relevance of 40
            'matching_points': matching_points if matching_points else [exp]
        })
    
    return results

def extract_achievements(experience: List[str]) -> List[str]:
    """Extract achievements with metrics from experience."""
    achievement_indicators = [
        r'\d+%', r'\$\d+', r'increased', r'decreased', r'improved',
        r'launched', r'led', r'managed', r'created', r'developed'
    ]
    
    achievements = []
    for exp in experience:
        if any(re.search(indicator, exp.lower()) for indicator in achievement_indicators):
            achievements.append(exp)
    
    return achievements[:3]

def generate_message(profile_sections: Dict[str, List[str]], 
                    target_position: str,
                    company_highlights: str,
                    tone: str,
                    message_length: str,
                    api_key: str) -> str:
    """Generate personalized message using free model."""
    try:
        # Detailed analysis
        experience_analysis = analyze_experience(profile_sections['experience'], target_position)
        achievements = extract_achievements(profile_sections['experience'])
        
        # Extract key information
        current_role = profile_sections['experience'][0] if profile_sections['experience'] else "Not specified"
        key_skills = ', '.join(profile_sections['skills'][:5]) if profile_sections['skills'] else "relevant skills"
        
        # Get most relevant experiences
        relevant_exp = [
            analysis['matching_points'][0] 
            for analysis in experience_analysis 
            if analysis['relevance'] > 60
        ]
        key_experience = '. '.join(relevant_exp) if relevant_exp else '. '.join(profile_sections['experience'][:2])
        
        # Construct prompt template
        prompt = f"""Write a {tone.lower()} LinkedIn recruitment message for a {target_position} position.
        Candidate currently works as: {current_role}
        Their key skills: {key_skills}
        Recent experience: {key_experience}
        Company details: {company_highlights}
        
        Requirements:
        1. Be {tone.lower()} and engaging
        2. Reference their specific experience
        3. Mention the opportunity clearly
        4. Include a call to action
        5. Keep it {message_length}
        
        Write the message:"""
        
        # Get response from free model
        message = query_free_model(prompt, api_key)
        
        # Format the message
        message = message.replace('\\n', '\n')
        if not message.startswith('Hi') and not message.startswith('Dear'):
            message = 'Hi [Name],\n\n' + message
        
        return message
    except Exception as e:
        st.error(f"Error generating message: {str(e)}")
        return None

def main():
    """Main application flow with free AI integration."""
    try:
        # Initialize session state
        if 'message_history' not in st.session_state:
            st.session_state.message_history = []

        st.title("Free AI Recruitment Message Generator")
        st.write("Generate personalized outreach messages using free AI models")

        # Sidebar settings
        with st.sidebar:
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
                - Include specific achievements
                - Add certifications
                - List key technologies
                - Mention team size and impact
                """)

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
                placeholder="E.g., Fast-growing startup, remote-first culture..."
            )

        with col2:
            target_position = st.text_input(
                "Target Position",
                help="Enter the position you're recruiting for"
            )
            
            if profile_text:
                st.markdown("### Profile Quality Check")
                sections = extract_profile_sections(profile_text)
                quality_score = sum([
                    len(sections['experience']) > 0,
                    len(sections['skills']) > 0,
                    len(sections['education']) > 0,
                    len(sections['summary']) > 0
                ]) * 25
                
                st.progress(quality_score / 100)
                st.text(f"Profile Completeness: {quality_score}%")
                
                if quality_score < 75:
                    st.warning("Add more profile details for better results")

        # Generate message
        if st.button("Generate Message") and profile_text and target_position:
            api_key = init_huggingface()
            profile_sections = extract_profile_sections(profile_text)
            
            with st.spinner("Generating personalized message..."):
                message = generate_message(
                    profile_sections,
                    target_position,
                    company_highlights,
                    tone,
                    message_length,
                    api_key
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

        # Setup instructions
        st.markdown("---")
        with st.expander("Installation & Usage Instructions"):
            st.markdown("""
            To run this app locally:
            
            1. Save this code as `app.py`
            2. Install required packages:
               ```bash
               pip install streamlit requests
               ```
            3. Optional: Create a free Hugging Face account and get an API token
            4. Create `.streamlit/secrets.toml`:
               ```toml
               HF_API_KEY = "your-huggingface-token"  # Optional
               ```
            5. Run the app:
               ```bash
               streamlit run app.py
               ```
            
            Note: Even without a Hugging Face token, the app will work with limited requests.
            """)

    except Exception as e:
        st.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()