import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000/api")


def get_headers():
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def ensure_login():
    if st.session_state.get("auth_token"):
        return True
    with st.form("login_form"):
        st.subheader("Login required")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")
    if submitted:
        resp = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            st.session_state["auth_token"] = token
            st.success("Logged in.")
            st.rerun()
        else:
            st.error("Invalid credentials.")
    return False

st.set_page_config(page_title="RFP Document Manager", page_icon="Document", layout="wide")

st.title("RFP Document Manager")

# Hide default helper text on file uploader (size/type hint)
st.markdown(
    """
    <style>
    div[data-testid="stFileUploader"] small {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not ensure_login():
    st.stop()

# Upload Section
st.header("Upload New Document")
st.caption("Accepted formats: PDF, DOCX")
uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"], label_visibility="collapsed")

if uploaded_file is not None:
    if st.button("Upload Document", type="primary"):
        with st.spinner("Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(f"{API_URL}/projects/upload", files=files, headers=get_headers())
            
            if response.status_code == 200:
                st.success("Document uploaded successfully.")
                st.rerun()
            else:
                st.error(f"Upload failed: {response.text}")

st.divider()

# Documents List Section
st.header("Uploaded Documents")

# Fetch all documents
try:
    response = requests.get(f"{API_URL}/documents", headers=get_headers())
    if response.status_code == 200:
        data = response.json()
        documents = data.get("documents", [])
        
        if not documents:
            st.info("No documents uploaded yet. Upload your first RFP document above!")
        else:
            # Display documents in a table with action buttons
            for doc in documents:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{doc['filename']}**")
                        upload_date = datetime.fromisoformat(doc['upload_date'].replace('Z', '+00:00'))
                        st.caption(f"Uploaded: {upload_date.strftime('%Y-%m-%d %H:%M')}")
                    
                    with col2:
                        if doc['has_analysis']:
                            st.success("Analyzed")
                        else:
                            st.warning("Not analyzed")
                    
                    with col3:
                        # Analyze button
                        if st.button("Analyze", key=f"analyze_{doc['id']}", disabled=False):
                            with st.spinner("Analyzing..."):
                                analyze_response = requests.post(
                                    f"{API_URL}/documents/{doc['id']}/analyze",
                                    headers=get_headers(),
                                )
                                if analyze_response.status_code == 200:
                                    st.success("Analysis complete!")
                                    st.rerun()
                                else:
                                    st.error(f"Analysis failed: {analyze_response.text}")
                    
                    with col4:
                        # View button - only enabled if analyzed
                        if doc['has_analysis']:
                            if st.button("View", key=f"view_{doc['id']}", type="primary"):
                                # Store project_id in session state and navigate
                                st.session_state['selected_project_id'] = doc['project_id']
                                st.switch_page("pages/1_Analysis_Review.py")
                        else:
                            st.button("View", key=f"view_{doc['id']}", disabled=True)
                    
                    st.divider()
    else:
        st.error("Failed to fetch documents")
except Exception as e:
    st.error(f"Error connecting to API: {str(e)}")

# Footer
st.markdown("---")
st.caption("RFP Agentic System - Multi-Agent Document Analysis")
