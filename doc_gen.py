#Final Version Ready for Deployment v5.1 18 June 2025

import streamlit as st
from docx import Document
import logging
import random
import pdfplumber
import json
import os
import zipfile
import pandas as pd
from doccreation import layout3, layout1, layout2 # docx templates for different layouts
from pydantic import BaseModel
from typing import List
from langchain.prompts import PromptTemplate
from LLMLab45 import LlamaLLM  # Your custom LLM wrapper

# Configure logging to enabled
logging.basicConfig(filename='resume_generator.log', level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')
 
# Define the Pydantic model for structured output
class Resume(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: str
    summary: str
    skills: List[str]
    certifications: List[str]
    experience: List[dict]
    education: List[dict]

# Prompt template for resume parsing
prompt_template = PromptTemplate(
    input_variables=["resume_text"],
    template="""
    Extract the following information from the resume:
    - Name
    - Email
    - Phone
    - Linkedin Look for any linkedin.com profile mentioned in the resume
    - Summary
    - Skills
    - Certifications
    - Experience with Roles and Responsibilities
    - Education OR Academic Profile
 
    Provide the output in JSON format with the following keys:
    - Name
    - Email
    - Phone
    - Linkedin
    - Summary
    - Skills
    - Certifications
    - Experience
    - Education
 
    For each experience, extract:
    - Title
    - Company
    - Duration
    - Roles and Responsibilities (as a list)
 
    For each education entry, extract:
    - Degree
    - Institution
    - Duration or Year
 
    Resume text:
    {resume_text}
    """
)
 
# Initialize LLM
llm = LlamaLLM()
 
def read_resume(uploaded_file):
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                #return "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
                text = ""
                for page in pdf.pages:
                    # Extract regular text
                    if page.extract_text():
                        text += page.extract_text() + "\n"
 
                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            text += "\t".join(cell if cell else "" for cell in row) + "\n"
            return text
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uploaded_file)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        else:
            raise ValueError("Unsupported file type")
    except Exception as e:
        logging.error(f"Error reading resume: {e}")
        st.error("Please try to upload again")
        return None

#New Code 
def parse_resume(resume_text):
    try:
        summarised_text = llm._call(
            "Kindly provide summary of profile, ensuring to include full name, email address, phone number, only single list of technical skills without categorizing, details of business capabilities, an overview of functional capabilities and complete professional experience along with roles and responsibilities if any,special notes read the entire profile before summarising as there can be multiple prifile formats emmeded one below another, Read profile till the end and the summarise" + resume_text,
            user="user"
        )
        formatted_prompt = prompt_template.format(resume_text=summarised_text)
        parsed_response = llm._call(prompt=formatted_prompt, user="user")
        #st.write(parsed_resume)

        if isinstance(parsed_response, tuple):
            parsed_response = parsed_response[0]

        if isinstance(parsed_response, dict) and "data" in parsed_response and "content" in parsed_response["data"]: # type: ignore
            parsed_text = parsed_response["data"]["content"] # type: ignore
        else:
            parsed_text = parsed_response

        if isinstance(parsed_text, str):
            parsed_text = parsed_text.strip()
            if parsed_text.startswith("```json"):
                parsed_text = parsed_text.replace("```json", "").strip()
            if parsed_text.endswith("```"):
                parsed_text = parsed_text.replace("```", "").strip()
                print(type(parsed_text))
            parsed_resume = json.loads(parsed_text)
            
            return parsed_resume
    except Exception as e:
        logging.error(f"Error parsing resume: {e}")
        st.error("Please try to upload again")
        return None
 
# ... [imports and initial setup remain unchanged] ...
 
# Helper function to generate and offer download
def generate_and_offer_download(parsed_result, layout_function):
    try:
        save_path = os.path.join(os.path.expanduser("~"), "Documents", "resumeparser")
        os.makedirs(save_path, exist_ok=True)
        resume_json = json.dumps(parsed_result)
        file_path = layout_function(resume_json, save_path)
 
        if file_path:
            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download",
                    data=f.read(),
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            #st.success("Resume generated and ready for download!")
        else:
            logging.error("Failed to generate resume. Please check the logs or try again.")
            st.error("Please try to upload again")
    except Exception as e:
        logging.error(f"Error generating or downloading resume: {e}")
        st.error("Please try to upload again")
 
# Layout selection functions
def option_one(parsed_result):
    st.success("Layout 1 selected!")
    generate_and_offer_download(parsed_result, layout1)
 
def option_two(parsed_result):
    st.success("Layout 2 selected!")
    generate_and_offer_download(parsed_result, layout2)  # Replace with layout2 if available
 
def option_three(parsed_result):
    st.success("Layout 3 selected!")
    generate_and_offer_download(parsed_result, layout3)  # Replace with layout3 if different
 
def generate_and_zip_resumes(parsed_results, layout_function, zip_file_name="resumes.zip"):
    try:
        save_path = os.path.join(os.path.expanduser("~"), "Documents", "resumeparser")
        os.makedirs(save_path, exist_ok=True)
 
        temp_dir = os.path.join(save_path, "temp_resumes")
        os.makedirs(temp_dir, exist_ok=True)
 
        for file_name, parsed_result in parsed_results:
            resume_json = json.dumps(parsed_result)
            layout_function(resume_json, temp_dir)
 
        zip_file_path = os.path.join(save_path, zip_file_name)
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)
 
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
 
        return zip_file_path
 
    except Exception as e:
        st.error(f"Error generating or zipping resumes: {e}")
        return None
 

def pd2csv(parsed_results):
    # Collect all flattened data
            combined_data = []

            for file_name, parsed_result in parsed_results:
                flat_data = {
                    "Name": parsed_result.get("Name", ""),
                    "Email": parsed_result.get("Email", ""),
                    "Phone": parsed_result.get("Phone", ""),
                    "Linkedin": parsed_result.get("Linkedin", ""),
                    "Summary": parsed_result.get("Summary", ""),
                    "Skills": ", ".join(parsed_result.get("Skills", [])),
                    "Certifications": ", ".join(
                        [str(cert) for cert in parsed_result.get("Certifications", []) if cert]
                            if isinstance(parsed_result.get("Certifications", []), list)
                            else [str(parsed_result.get("Certifications", ""))]
                        ),
                    "Experience": "; ".join(
                        [f"{exp.get('Title', '')} at {exp.get('Company', '')} ({exp.get('Duration', '')})"
                            for exp in parsed_result.get("Experience", []) if isinstance(exp, dict)]
                        ),
                    "Education": "; ".join(
                        [f"{edu.get('Degree', '')} from {edu.get('Institution', '')} ({edu.get('Duration', '')})"
                            for edu in parsed_result.get("Education", [])
                                if isinstance(edu, dict)]
                        ) if isinstance(parsed_result.get("Education"), list) else str(parsed_result.get("Education", ""))

                }
                combined_data.append(flat_data)

            # Create a single DataFrame
            combined_df = pd.DataFrame(combined_data)

            # Display the combined DataFrame
            st.markdown("## 📊 Parsed Data Table")
            st.dataframe(combined_df, use_container_width=True, hide_index=True)
            csv = combined_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download as CSV",
                data=csv,
                file_name="Consolidated_Resumes.csv",
                mime="text/csv"
            )

# Image layout options
images = [
    ("Kallisti", "./New folder/Layout1.png", option_one),
    ("Phaedon", "./New folder/Layout2.png", option_two),
    ("Erasmos", "./New folder/Layout3.png", option_three),
]

# Recruit Agent
def recruit_agent():
        st.markdown("### 👥 Recruitment Agent")
        st.write("Generate a structured profile using the selected layout for a given profile.")
        #st.markdown("<h1 style='font-size: 30px;'>📄 Recruitment Agent</h1>", unsafe_allow_html=True)
        st.markdown("<h8 style='font-size: 16px;'>Upload your resume</h8>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Upload your resume", label_visibility="collapsed", type=[ "pdf", "docx"], accept_multiple_files=True)
    
        #parsed_result = None
        #Enabled multi-upload
        parsed_results = []
        error_logs = []
        
        if uploaded_files:
            progress_bar = st.progress(0)
            total_files = len(uploaded_files)
        
            for idx, uploaded_file in enumerate(uploaded_files):
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        resume_text = read_resume(uploaded_file)
                        if not resume_text:
                            raise ValueError("Empty or unreadable resume text.")
        
                        parsed_result = parse_resume(resume_text)
                        if not parsed_result:
                            raise ValueError("Parsing returned no result.")
        
                        parsed_results.append((uploaded_file.name, parsed_result))
                    except Exception as e:
                        error_logs.append((uploaded_file.name, str(e)))
        
                # Update progress bar
                progress_bar.progress((idx + 1) / total_files)
        
            progress_bar.empty()  # Remove the progress bar after completion
        
        # Display error summary
        if error_logs:
            st.markdown("## ⚠️ Error Summary")
            for filename, error in error_logs:
                st.error(f"❌ {filename}: {error}")
        
        # if uploaded_file is not None:
        #     with st.spinner("Reading and parsing resume..."):
        #         resume_text = read_resume(uploaded_file)
        #         if resume_text:
        #             parsed_result = parse_resume(resume_text)
        
        # Helper function to generate and offer download
    

        if parsed_results:
            for file_name, parsed_result in parsed_results:
                #st.markdown(f"### Parsed Result for: {file_name}")
                #st.json(parsed_result)
        
                if isinstance(parsed_result, str):
                    try:
                        parsed_result = json.loads(parsed_result)
                    except json.JSONDecodeError as e:
                        st.error(f"Failed to decode parsed result: {e}")
                        st.stop()
            
                if not isinstance(parsed_result, dict):
                    st.error("Parsed result is not a dictionary. Cannot proceed.")
                    st.stop()
            
                if 'Name' not in parsed_result:
                    st.error("The 'Name' field is missing in the parsed result.")
                    st.stop()


        # Layout selection UI
        if parsed_results:
            st.markdown("<h8 style='font-size: 16px;'>Choose a Layout:</h8>", unsafe_allow_html=True)
            cols = st.columns(3, vertical_alignment="center")
            for i, (title, img_path, func) in enumerate(images):
                with cols[i]:
                    st.image(img_path, use_container_width=False)
                    if st.button(f"Layout: {title}", use_container_width=True, disabled=True): #key=f"{random.randint(0, 10000)}"):
                        print("") 
        
        # Bulk download section
        if parsed_results:
            layout_options = {
                "Kallisti (Layout 1)": layout1,
                "Phaedon (Layout 2)": layout2,
                "Erasmos (Layout 3)": layout3
            }
            selected_layout_label = st.selectbox("📄 Select a layout for all resumes", list(layout_options.keys()))
            selected_layout_function = layout_options[selected_layout_label]
        
            st.markdown("<h8 style='font-size: 16px;'> 📦 Download All Resumes as ZIP</h8>", unsafe_allow_html=True)
            zip_file_path = generate_and_zip_resumes(parsed_results, selected_layout_function)
            if zip_file_path:
                with open(zip_file_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download All Resumes",
                        data=f.read(),
                        file_name=os.path.basename(zip_file_path),
                        mime="application/zip"
                    )
        return parsed_results
