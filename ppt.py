import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import pdfplumber
import json
import os
import zipfile
from generate_resume import layout3, layout1, layout2
from pptcreation import layout5
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
     
#logo
image_path= r"D:\OneDrive - Wipro\Desktop\Trainng-Perl_Python\Python_Codes\LLM_USE Cases\Resume_Parser\New folder\\Wipro_Primary Logo_Color_RGB.png"
# Prompt template for resume parsing
prompt_template = PromptTemplate(
    input_variables=["resume_text"],
    template="""
Extract the following information from the resume:
 
- Name
- Email
- Phone
- Linkedin (look for any linkedin.com profile or link mentioned in the Profile)
- Summary (summarize within 500 characters)
- Roles Played
- Areas of Expertise
- Skills (Populate Top 15 skills based on your understanding of the complete profile)
- Industry Sectors
- Consulting Engagements (Only take the Top 5 engagements name where person have performed a Consultant role as per profile)
- Education or Academic Profile and Certifications
- Experience and Accomplishments
 
Provide the output in JSON format with the following keys:
- Name
- Email
- Phone
- Linkedin
- Summary
- Roles Played
- Areas of Expertise
- Skills
- Industry Sectors
- Consulting Engagements
- Education or Academic Profile and Certifications
- Experience and Accomplishments
 
### Parsing Instructions:
 
**Roles Played**:
- From the experience section, extract all distinct roles the individual has held.
 
**Industry Sectors**:
- From the experience section, identify the domains or industries the individual has worked in (e.g., Healthcare, Finance, Retail).
 
**Areas of Expertise**:
- Identify domains, technologies, methodologies, or roles the individual has demonstrated experience in.
- Focus on what they have done, built, led, or contributed to.
- Present the output as a list of implicit areas of expertise, grouped by category if possible (e.g., Technical Domains, Tools & Technologies, Business Functions, etc.).
 
**Experience and Accomplishments**:
For each professional experience listed in the resume, extract the following details:
- Title
- Company
- Duration
- Location (if available)
- Detailed Roles and Responsibilities:
    - List each responsibility as a separate bullet point.
    - Include both technical and managerial responsibilities.
    - Capture any leadership, mentoring, or cross-functional collaboration.
    - Include tools, technologies, or methodologies used.
    - If achievements or outcomes are mentioned (e.g., improved performance, cost savings), include them as part of the responsibility.
    - Maintain the original context and phrasing as much as possible, but ensure clarity.
    - Ensure completeness—do not summarize or omit relevant details.
 
**Education or Academic Profile and Certifications**:
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
        summarised_response = llm._call(
            "Kindly provide summary of profile, ensuring to include full name, email address, phone number, only single list of technical skills without categorizing, details of business capabilities, an overview of functional capabilities and complete professional experience along with roles and responsibilities if any, special notes read the entire profile before summarising as there can be multiple profile formats embedded one below another. Read profile till the end and then summarise." + resume_text,
            user="user"
        )
 
        if isinstance(summarised_response, tuple):
            summarised_response = summarised_response[0]
 
        if isinstance(summarised_response, dict) and "data" in summarised_response and "content" in summarised_response["data"]: # type: ignore
            summarised_text = summarised_response["data"]["content"] # type: ignore
        else:
            summarised_text = summarised_response  # fallback if already a string
 
        formatted_prompt = prompt_template.format(resume_text=summarised_text)
        parsed_response = llm._call(prompt=formatted_prompt, user="user")
 
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
           
        else:
            raise ValueError("Parsed content is not a string")
 
        return parsed_resume
 
    except json.JSONDecodeError as e:
        st.error(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        st.error(f"Error parsing resume: {e}")
        return None


def generate_and_offer_download(parsed_result, layout_function):
    try:
        save_path = os.path.join(os.path.expanduser("~"), "Documents", "resumeparser")
        os.makedirs(save_path, exist_ok=True)
        resume_json = json.dumps(parsed_result)
        #st.json(resume_json)
        file_path = layout_function(resume_json, save_path, image_path)
        #st.write(file_path)
        if file_path:
            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download",
                    data=f.read(),
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            st.balloons()
            #st.success("Resume generated and ready for download!")
        else:
            st.error("Failed to generate resume. Please check the logs or try again.")
    except Exception as e:
        st.error(f"Error generating or downloading resume: {e}")
 
def generate_and_zip_resumes(parsed_results, layout_function, zip_file_name="resumes.zip"):
    try:
        save_path = os.path.join(os.path.expanduser("~"), "Documents", "resumeparser")
        os.makedirs(save_path, exist_ok=True)
 
        temp_dir = os.path.join(save_path, "temp_resumes")
        os.makedirs(temp_dir, exist_ok=True)
 
        for file_name, parsed_result in parsed_results:
            resume_json = json.dumps(parsed_result)
            layout_function(resume_json, temp_dir, image_path)
 
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
 
# Layout selection functions
def option_one(parsed_result):
    st.success("Layout 1 selected!")
    generate_and_offer_download(parsed_result, layout5)
 
def option_two(parsed_result):
    st.success("Layout 2 selected!")
    generate_and_offer_download(parsed_result, layout2)  # Replace with layout2 if available
 
def option_three(parsed_result):
    st.success("Layout 3 selected!")
    generate_and_offer_download(parsed_result, layout3)  # Replace with layout3 if different
 
# Image layout options
images = [
    ("Kallisti", r"D:\OneDrive - Wipro\Desktop\Trainng-Perl_Python\Python_Codes\LLM_USE Cases\Resume_Parser\New folder\\Layout1.png", option_one),
    ("Phaedon", r"D:\OneDrive - Wipro\Desktop\Trainng-Perl_Python\Python_Codes\LLM_USE Cases\Resume_Parser\New folder\\Layout2.png", option_two),
    ("Erasmos", r"D:\OneDrive - Wipro\Desktop\Trainng-Perl_Python\Python_Codes\LLM_USE Cases\Resume_Parser\New folder\\Layout3.png", option_three),
]

def ppt_call(): 
    # Streamlit UI
    #st.markdown("<h1 style='font-size: 30px;color:#4F81BD;'>Resume Parser📄</h1>", unsafe_allow_html=True)
    st.markdown("<h8 style='font-size: 16px;'>Upload your resume</h8>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload your resume", label_visibility="collapsed", type=["txt", "pdf", "docx"], accept_multiple_files=True)
    
    #parsed_result = None
    #Enabled multi-upload
    parsed_results = []
    error_logs = []
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
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
            st.markdown(f"### Parsed Result for: {file_name}")
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
            st.markdown("<h8 style='font-size: 16px;'>Choose a Layout:</h8>", unsafe_allow_html=True)
            cols = st.columns(3, vertical_alignment="center")
            for i, (title, img_path, func) in enumerate(images):
                with cols[i]:
                    st.image(img_path, use_container_width=False)
                    if st.button(f"Layout: {title}", use_container_width=True):
                        func(parsed_result)
    
    # Bulk download section
    if parsed_results:
        layout_options = {
            "Kallisti (Layout 1)": layout5,
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