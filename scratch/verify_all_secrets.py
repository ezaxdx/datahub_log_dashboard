import sys
import os

# Add the directory to path
sys.path.append(os.getcwd())

try:
    import streamlit as st
    # Mocking streamlit environment to test secrets loading
    # Streamlit looks for .streamlit/secrets.toml automatically when streamlit is imported or used
    
    import data
    print("Attempting to initialize data load (dry run of connection)...")
    # We won't actually call load_all() because it might require network or browser,
    # but we can check if it gets the right creds from st.secrets.
    
    if "gcp_service_account" in st.secrets:
        print("SUCCESS: gcp_service_account found in st.secrets")
    else:
        print("FAILED: gcp_service_account NOT found")
        
    if "smtp" in st.secrets:
        print("SUCCESS: smtp found in st.secrets")
    else:
        print("FAILED: smtp NOT found")

except Exception as e:
    print(f"Error during verification: {e}")
