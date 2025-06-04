#Final Version Ready for Deployment v2.1 27 May 2025

import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import pdfplumber
import json
import os
from generate_resume import layout3, layout1, layout2
from pydantic import BaseModel
from typing import List
from langchain.prompts import PromptTemplate
from LLMLab45 import LlamaLLM  # Your custom LLM wrapper
 
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
        st.error(f"Error reading resume: {e}")
        return None
 
def parse_resume(resume_text):
    try:
        summarised_text = llm._call(
            "Kindly provide summary of profile, ensuring to include full name, email address, phone number, only single list of technical skills without categorizing, details of business capabilities, an overview of functional capabilities and complete professional experience along with roles and responsibilities if any,special notes read the entire profile before summarising as there can be multiple prifile formats emmeded one below another, Read profile till the end and the summarise" + resume_text,
            user="user"
        )
        formatted_prompt = prompt_template.format(resume_text=summarised_text)
        parsed_response = llm._call(prompt=formatted_prompt, user="user")
        #st.write(parsed_resume)
 
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
        st.error(f"Error parsing resume: {e}")
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
            st.error("Failed to generate resume. Please check the logs or try again.")
    except Exception as e:
        st.error(f"Error generating or downloading resume: {e}")
 
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
 
# Image layout options
images = [
    ("Kallisti", "./New folder/Layout1.png", option_one),
    ("Phaedon", "./New folder/Layout2.png", option_two),
    ("Erasmos", "./New folder/Layout3.png", option_three),
]
 
# Streamlit UI

st.set_page_config(page_title='Resume Parser', initial_sidebar_state = 'auto')
st.markdown("<h1 style='font-size: 30px;color:#4F81BD;'>Resume Parser📄</h1>", unsafe_allow_html=True)
st.markdown("<h8 style='font-size: 16px;color:#17365D;'>Upload your resume</h8>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload your resume", label_visibility="collapsed", type=["txt", "pdf", "docx"])
 
parsed_result = None
 
if uploaded_file is not None:
    with st.spinner("Reading and parsing resume..."):
        resume_text = read_resume(uploaded_file)
        if resume_text:
            parsed_result = parse_resume(resume_text)
 
if parsed_result:
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
    st.markdown("<h8 style='font-size: 16px;color:#17365D;'>Choose a Layout:</h8>", unsafe_allow_html=True)
    cols = st.columns(3, vertical_alignment="center")
    for i, (title, img_path, func) in enumerate(images):
        with cols[i]:
            st.image(img_path, use_container_width=False)
            if st.button(f"Layout: {title}", use_container_width=True):
                func(parsed_result)
 