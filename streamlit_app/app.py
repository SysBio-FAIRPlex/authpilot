import streamlit as st
import uuid
import requests
from urllib.parse import urlencode

AUTH_URL = "https://auth-344651184654.us-central1.run.app/"
SYSBIO_SEARCH_URL = "https://sysbio-344651184654.us-central1.run.app/"

# AUTH_URL = "http://localhost:8003"
# SYSBIO_SEARCH_URL = "http://localhost:8000"

# Step 1: # Get the authorization code from the URL
query_params = st.query_params
auth_code = query_params.get("code")

# Step 2: If state is lost from session, recover it from the URL
if "state" not in st.session_state:
    # Check if we are returning from a redirect with the state in the URL
    if "state" in query_params:
        st.session_state.state = query_params["state"]
    # Otherwise, it's a new session, so create a new state
    else:
        st.session_state.state = str(uuid.uuid4())

# Always sync the URL to match the session state, unless we just arrived from redirect
if not auth_code:
    st.query_params["state"] = st.session_state.state


# Step 3: Use the state for session lookup
state = st.session_state.state
returned_state = query_params.get("state")

# Step 4: Check for an access token or attempt to get one
if auth_code:
    # Security check: The state from the URL must match the one in our session
    if returned_state != state:
        st.error(f"STATE mismatch. Authentication failed. Please try again.")
        st.write(f"Expected: `{state}`")
        st.write(f"Received: `{returned_state}`")
        st.stop()
    session_url = f"{AUTH_URL}/session?state={state}"
    response = requests.get(session_url)
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
                    "query": "SELECT * FROM person LIMIT 10",
                    # NOTE - These parameters are inteded for DEMO PURPOSES ONLY
                    # In reality, the service will automatically check the credentials of the user
                    # via ga4gh passport/visa to see if they have access to the datasets.
                    "parameters": {
                        "pd_access": True,
                        "ad_access": True
                    }
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
    st.query_params.clear()  # Clear state from URL
    st.rerun()
