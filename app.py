import streamlit as st
import re
from typing import Dict, List

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
    
    # Split text into lines and process
    lines = profile_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Identify sections based on common LinkedIn headers
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
            
        # Add content to appropriate section
        if current_section:
            if current_section == 'summary':
                sections[current_section] += line + ' '
            else:
                sections[current_section].append(line)
    
    return sections

def generate_outreach_message(profile_sections: Dict[str, List[str]], target_position: str) -> str:
    """
    Generate a personalized outreach message based on profile sections and target position.
    """
    # Extract name (assuming it's the first line of experience or summary)
    name = "the candidate"
    if profile_sections['experience']:
        name_match = re.search(r'^([A-Za-z]+(?:\s[A-Za-z]+)?)', profile_sections['experience'][0])
        if name_match:
            name = name_match.group(1)
    
    # Extract current role
    current_role = "professional"
    if profile_sections['experience']:
        current_role = profile_sections['experience'][0].split(' at ')[0]
    
    # Extract relevant skills
    skills = profile_sections['skills'][:3] if profile_sections['skills'] else []
    skills_str = ", ".join(skills) if skills else "relevant experience"
    
    # Generate message
    message = f"""Hi {name},

I hope this message finds you well! I'm a technical recruiter and I came across your profile. I'm particularly impressed by your experience as a {current_role} and your expertise in {skills_str}.

We have an exciting opportunity for a {target_position} role that I believe would be a great fit for someone with your background. I'd love to connect and share more details about this position and learn about your career interests.

Would you be open to a brief conversation about this opportunity?

Looking forward to hearing from you!

Best regards"""
    
    return message

# Streamlit UI
st.title("LinkedIn Outreach Message Generator")
st.write("Generate personalized recruitment messages based on LinkedIn profiles")

# Input sections
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
    - Make sure sections like Experience, Education, and Skills are included
    - Keep section headers in their original format
    """)

# Generate button
if st.button("Generate Message") and profile_text and target_position:
    # Process profile and generate message
    profile_sections = extract_profile_sections(profile_text)
    message = generate_outreach_message(profile_sections, target_position)
    
    # Display generated message
    st.markdown("### Generated Message:")
    st.text_area("", message, height=300)
    
    # Add copy button
    st.markdown("Click the copy icon in the top-right of the message box to copy to clipboard")
    
    # Display extracted sections for verification
    with st.expander("View Extracted Profile Sections"):
        for section, content in profile_sections.items():
            st.markdown(f"**{section.title()}:**")
            if isinstance(content, list):
                for item in content:
                    st.markdown(f"- {item}")
            else:
                st.markdown(content)

# Add instructions for installation and running
st.markdown("---")
with st.expander("Installation & Usage Instructions"):
    st.markdown("""
    To run this app locally:
    
    1. Save this code in a file named `app.py`
    2. Install required package:
       ```
       pip install streamlit
       ```
    3. Run the app:
       ```
       streamlit run app.py
       ```
    4. The app will open in your default web browser
    """)
