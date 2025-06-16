import streamlit as st
import uuid
import requests
from urllib.parse import urlencode

AUTH_URL = "https://auth-344651184654.us-central1.run.app/"
SYSBIO_SEARCH_URL = "https://sysbio-344651184654.us-central1.run.app/"

# Step 1: Check URL params for existing state
query_params = st.query_params
url_state = query_params.get("state", [None])[0]

# Step 2: Use the state from URL if available, else create and update URL
if url_state:
    st.session_state.state = url_state
else:
    st.session_state.state = str(uuid.uuid4())
    new_url = f"?{urlencode({'state': st.session_state.state})}"
    st.query_params = { "state": st.session_state.state }
    st.rerun()  # Force reload with updated URL

# Step 3: Use the state for session lookup
state = st.session_state.state
session_url = f"{AUTH_URL}/session?state={state}"
response = requests.get(session_url)

# Step 4: Display based on session result
if response.ok and response.json():
    data = response.json()
    access_token = data.get("access_token")
    st.session_state.access_token = access_token
    st.success("Access token retrieved!")
    st.json(data)
else:
    params = {
        "state": state,
        "redirect_uri": "http://localhost:8501" # The URL of my streamlit app
    }
    encoded_params = urlencode(params)
    login_url = f"{AUTH_URL}/login?{encoded_params}"
    st.markdown(f"[Login with Google]({login_url})", unsafe_allow_html=True)

if "access_token" in st.session_state:
    access_token = st.session_state.access_token

    # Display token and button
    st.write("Access token:")
    st.code(access_token)

    if st.button("Make Search Request"):
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        try:
            response = requests.post(
                f"{SYSBIO_SEARCH_URL}/search",
                headers=headers,
                json={
                    "query": "SELECT * FROM person LIMIT 10"
                }
            )
            if response.ok:
                st.success("Search request successful")
                st.json(response.json())
            else:
                st.error(f"Request failed: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Error during request: {str(e)}")

if st.button("Logout"):
    for key in ["access_token", "state"]:
        if key in st.session_state:
            del st.session_state[key]
    st.query_params = {}  # Clear state from URL
    st.rerun()
