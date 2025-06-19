#Final Version Ready for Deployment v5.1 18 June 2025

import streamlit as st
import logging

import bcrypt
from doc_gen import recruit_agent
import ppt
from pydantic import BaseModel

from dotenv import dotenv_values, set_key
import os

# Define the path to the .env file
env_path = ".env"

def set_env(token):
    # Define the new or updated environment variables
    new_env_vars = {
        "TOKEN": f"Bearer {token}"
    }

    # Load existing environment variables from the .env file
    if os.path.exists(env_path):
        existing_env = dotenv_values(env_path)
    else:
        existing_env = {}

    # Update or add new environment variables
    for key, value in new_env_vars.items():
        set_key(env_path, key, value)

    # Confirm update
    print(f".env file has been updated with the following variables:\n{new_env_vars}")


# Configure logging to enabled
logging.basicConfig(filename='resume_generator.log', level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')
 
# Define the Pydantic model for structured output
class User(BaseModel):
    username: str
    password: str

# Password hashing helpers
def hash_password(password: str) -> str:
 return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
 return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

user = User(username="admin", password="password123")

# Recruit Agent
def show_recruit_agent():
        recruit_agent()

# Sales Agent
def show_sales_agent():
        st.markdown("### 📈 Sales Agent Page")
        st.write("Generate a one-slide PowerPoint presentation for the given profile.")
        ppt.ppt_call()

# Admin Page
def show_admin_page():
   st.title("Admin Page")
   st.subheader("Add New User")
   new_username = st.text_input("New Username", key="new_username")
   new_password = st.text_input("New Password", type="password", key="new_password")
   if st.button("Add User"):
       if new_username and new_password:
           hashed_pw = hash_password(new_password)
           st.session_state.users[new_username] = new_password
           st.success(f"User '{new_username}' added successfully.")
       else:
           st.error("Please enter both username and password.")

   st.subheader("Add Token")
   new_token = st.text_input("New Token", key="new_token")
   if st.button("Add Token"):
       if new_token:
           st.session_state.tokens.append("Bearer " + new_token)
           set_env(new_token)
           st.success("Token added successfully.")
       else:
           st.error("Please enter a token.")

   st.write("Current Tokens:")
   for token in st.session_state.tokens:
       st.write(f"- {token}")

   if st.button("Back to Welcome Page"):
       st.session_state.page = "Welcome Page"

# Welcome page
def show_welcome_page():  
    if st.session_state.page == "Welcome":
        st.session_state.page = "Welcome"
    st.sidebar.markdown("## 📋 Navigation")
    pages = ["Welcome", "Recruitment Agent", "Sales Agent", "Build Your Resume(WIP)"]
    if st.session_state.username == "admin":
        pages.append("Admin")

    page = st.sidebar.radio("Go to", pages)
    # Page Routing
    if page == "Welcome":
        st.session_state.page = "Welcome"
        st.markdown("### 🤖 Welcome to LLM - Powered TalentStream Pro!")
        st.markdown(
        "<br> <br> A cutting-edge solution using advanced LLM technology to automate resume extraction and streamline document formatting for recruitment and sales support. <br> The system offers three predefined document formats, ensuring consistency and efficiency for agents. It also supports sales teams in creating one-slide PowerPoint presentations for RFPs. <br> In an upcoming enhancement, users will have the option to upload custom templates for automatic conversion of resumes. TalentStream Pro revolutionizes recruitment and sales processes, enhancing overall efficiency and consistency.",unsafe_allow_html=True)
    elif page == "Recruitment Agent":
        show_recruit_agent()
    elif page == "Sales Agent":
        show_sales_agent()
    elif page == "Build Your Resume(WIP)":
        st.markdown("### 📝 Build Your Resume")
        st.write("This feature will allow you to create a resume from scratch.")
    elif page == "Admin":
        st.session_state.page = "Admin"
        show_admin_page()
    
    #st.sidebar.info("Use this panel to navigate or view instructions.")
    st.sidebar.markdown("### 🔍 Instructions")
    st.sidebar.write("""
    1. Upload your resume in PDF, DOCX format.
    2. Wait for the resume to be parsed.
    3. Choose your preferred layout.
    4. Download the generated resume.
    """)
    st.sidebar.markdown("### 👤 Logged in as: `" + st.session_state.username + "`")   

def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])  # Center the input box

    with col2:
        st.markdown("#### Welcome to TalentStream Pro")
        user_name = st.text_input("Username", key="user_name")
        pass_word = st.text_input("Password", type="password", key="pass_word")

        if st.button("Login"):
            if user_name in st.session_state.users and check_password(pass_word, st.session_state.users[user_name]):
                st.session_state.logged_in = True
                st.session_state.username = user_name
                st.session_state.page = "Welcome"
            else:
                st.error("Invalid username or password")


# Streamlit UI
st.set_page_config(page_title='TalentStream Pro', initial_sidebar_state = 'auto')

# Initialize session state variables
if 'logged_in' not in st.session_state:
       st.session_state.logged_in = False
if 'username' not in st.session_state:
       st.session_state.username = ""
if 'users' not in st.session_state:
    st.session_state.users = {
        "admin": hash_password("password123"),
        "krishnakanth": hash_password("password123"),
        "manish": hash_password("password123")
    }

if 'tokens' not in st.session_state:
       st.session_state.tokens = []

if "page" not in st.session_state:
       st.session_state.page = "Welcome"


# Display appropriate page
if st.session_state.logged_in:
    show_welcome_page()
else:
    show_login_page()





