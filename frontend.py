import streamlit as st
import requests
import uuid
# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Character AI", page_icon="🤖", layout="wide")

# --- 1. PERSISTENCE SETUP (Fixes Refresh Issue) ---
# We check the URL for a token. If found, we restore the session.
query_params = st.query_params
if "token" in query_params and "token" not in st.session_state:
    st.session_state.token = query_params["token"]
    st.session_state.username = query_params.get("username", "User")
    st.rerun() # Refresh to apply state
 
# --- SESSION STATE INITIALIZATION ---
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = "Guest"
if "current_view" not in st.session_state:
    st.session_state.current_view = "dashboard"
if "selected_char" not in st.session_state:
    st.session_state.selected_char = None
if "guest_id" not in st.session_state:
    st.session_state.guest_id = f"guest_{uuid.uuid4().hex[:8]}"
# --- HELPER FUNCTIONS ---
def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}" if st.session_state.token else "","X-Guest-ID": st.session_state.guest_id  # <--- NEW: Send the badge!
    }
def set_login_state(token, username):
    st.session_state.token = token
    st.session_state.username = username
    # Save to URL so F5 refresh doesn't kill login
    st.query_params["token"] = token
    st.query_params["username"] = username

def logout():
    st.session_state.clear() # WIPE EVERYTHING (Fixes Ghost Chats)
    st.query_params.clear()  # Clean URL
    st.rerun()

def fetch_chat_history(char_id):
    """
    Forces a fresh fetch from the DB every time we open a chat.
    This fixes the 'Missing History' and 'Wrong User' bugs.
    """
    try:
        # Thread ID is hardcoded to "1" for V1 simplicity
        res = requests.get(f"{API_URL}/chat/{char_id}/1", headers=get_headers())
        if res.status_code == 200:
            history = res.json()
            # If backend returns "No history", return empty list
            if isinstance(history, dict) and "message" in history:
                return []
            return history
    except Exception:
        return []
    return []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🤖 AI Companions")
    
    if st.session_state.token:
        st.success(f"Logged in as: **{st.session_state.username}**")
        
        if st.button("🏠 Dashboard"):
            st.session_state.current_view = "dashboard"
            st.rerun()
            
        if st.button("➕ Create Character"):
            st.session_state.current_view = "create"
            st.rerun()
            
        st.divider()
        if st.button("Logout", type="primary"):
            logout()
            
    else:
        st.info("Guest Mode")
        st.warning("Chats will not saved in Guest Mode.")
        
        tab1, tab2 = st.tabs(["Login", "Signup"])
        with tab1:
            l_user = st.text_input("Username", key="l_user")
            l_pass = st.text_input("Password", type="password", key="l_pass")
            if st.button("Log In"):
                try:
                    res = requests.post(f"{API_URL}/token", data={"username": l_user, "password": l_pass})
                    if res.status_code == 200:
                        set_login_state(res.json()["access_token"], l_user)
                        st.success("Success!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                except Exception as e:
                    st.error(f"Error: {e}")
        with tab2:
            s_user = st.text_input("New Username", key="s_user")
            s_pass = st.text_input("New Password", type="password", key="s_pass")
            if st.button("Sign Up"):
                try:
                    res = requests.post(f"{API_URL}/signup", json={"username": s_user, "password": s_pass})
                    if res.status_code == 200:
                        st.success("Created! You can now log in.")
                    else:
                        st.error(res.json().get("detail", "Error"))
                except:
                    st.error("Connection failed")

# --- DASHBOARD ---
if st.session_state.current_view == "dashboard":
    st.header("Select a Character")
    try:
        res = requests.get(f"{API_URL}/chat/all_characters")
        if res.status_code == 200:
            chars = res.json()
            cols = st.columns(3)
            for idx, char in enumerate(chars):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(char["name"])
                        st.caption(char['prompt_data'].get('CHAR_ROLE', 'Unknown'))
                        
                        if st.button(f"Chat", key=f"chat_{char['id']}"):
                            st.session_state.selected_char = char
                            st.session_state.current_view = "chat"
                            st.rerun()
                            
                        # Delete Button (Only works if you own it)
                        if st.session_state.token:
                             if st.button("🗑️", key=f"del_{char['id']}"):
                                d_res = requests.delete(f"{API_URL}/character/delete-character/{char['id']}", headers=get_headers())
                                if d_res.status_code == 200:
                                    st.success("Deleted")
                                    st.rerun()
                                else:
                                    st.error("Not your character!")
    except Exception as e:
        st.error(f"API Error: {e}")

# # --- CREATE CHARACTER ---
# elif st.session_state.current_view == "create":
#     st.header("Create New Character")
#     with st.form("new_char"):
#         cid = st.text_input("ID (unique)", placeholder="e.g. ironman")
#         name = st.text_input("Name", placeholder="Iron Man")
#         role = st.text_input("Role")
#         desc = st.text_area("Description/Prompt")
#         if st.form_submit_button("Create"):
#             payload = {
#                 "char_id": cid, "name": name,
#                 "prompt_data": {
#                     "CHAR_NAME": name, "CHAR_ROLE": role, 
#                     "CHAR_AGE": "30", "CHAR_APPEARANCE": "Unknown", 
#                     "CHAR_PERSONALITY": desc, "CHAR_BACKSTORY": "Unknown", 
#                     "SPEAKING_STYLE": "Normal", "CHAR_QUIRKS": "None", 
#                     "CHAR_TONE": "Normal", "CURRENT_SETTING": "Chat", 
#                     "USER_RELATIONSHIP": "Stranger", "CHAR_GOAL": "Chat"
#                 }
#             }
#             res = requests.post(f"{API_URL}/create-character", json=payload, headers=get_headers())
#             if res.status_code == 200:
#                 st.session_state.current_view = "dashboard"
#                 st.rerun()
#             else:
#                 st.error("Failed. ID might be taken.")
# --- VIEW 2: CREATE CHARACTER ---
elif st.session_state.current_view == "create":
    st.header("Create a New Character")
    st.info("Fill in the details below to define exactly how your AI character behaves.")

    with st.form("create_char_form"):
        # --- Section 1: Basic Identity ---
        st.subheader("1. Identity")
        col1, col2 = st.columns(2)
        with col1:
            char_id = st.text_input("Unique ID (e.g., batman)", placeholder="one-word-id")
            name = st.text_input("Display Name", placeholder="Batman")
            role = st.text_input("Role / Occupation", placeholder="Vigilante Detective")
        with col2:
            age = st.text_input("Age", placeholder="35")
            appearance = st.text_area("Physical Description", placeholder="Tall, muscular, wears a bat cowl...", height=100)

        st.divider()

        # --- Section 2: Personality & Lore ---
        st.subheader("2. Personality & Lore")
        personality = st.text_area("Personality & Psyche", placeholder="Brooding, intelligent, paranoid, determined...", height=100)
        backstory = st.text_area("Backstory", placeholder="Witnessed parents' death, trained by ninjas...", height=100)

        st.divider()

        # --- Section 3: Communication Style ---
        st.subheader("3. Speaking Style")
        c1, c2, c3 = st.columns(3)
        with c1:
            style = st.text_input("Speaking Style", placeholder="Gruff, terse, deep voice")
        with c2:
            tone = st.text_input("Tone", placeholder="Serious, intimidating")
        with c3:
            quirks = st.text_input("Quirks/Catchphrases", placeholder="Says 'I am Batman' often")

        st.divider()

        # --- Section 4: The Scenario ---
        st.subheader("4. The Scenario")
        setting = st.text_input("Current Setting", placeholder="The Batcave, rainy night")
        
        sc1, sc2 = st.columns(2)
        with sc1:
            rel = st.text_input("Relationship to User", placeholder="Stranger / Butler / Enemy")
        with sc2:
            goal = st.text_input("Immediate Goal", placeholder="Solve the riddle")

        st.divider()

        submitted = st.form_submit_button("Create Character", type="primary")
        
        # if submitted:
        #     # Check strictly for ID and Name (others can technically be empty, but better if filled)
        #     if not char_id or not name:
        #         st.error("Character ID and Name are required.")
        #     else:
        #         # Construct the Payload matching your Pydantic 'PromptData' model perfectly
        #         payload = {
        #             "char_id": char_id.lower().strip(), # Clean up ID
        #             "name": name,
        #             "prompt_data": {
        #                 "CHAR_NAME": name,
        #                 "CHAR_ROLE": role,
        #                 "CHAR_AGE": age,
        #                 "CHAR_APPEARANCE": appearance,
        #                 "CHAR_PERSONALITY": personality,
        #                 "CHAR_BACKSTORY": backstory,
        #                 "SPEAKING_STYLE": style,
        #                 "CHAR_QUIRKS": quirks,
        #                 "CHAR_TONE": tone,
        #                 "CURRENT_SETTING": setting,
        #                 "USER_RELATIONSHIP": rel,
        #                 "CHAR_GOAL": goal
        #             }
        #         }
                
        #         try:
        #             res = requests.post(f"{API_URL}/create-character", json=payload, headers=get_headers())
                    
        #             if res.status_code == 200:
        #                 st.success(f"🎉 Character '{name}' created successfully!")
        #                 # Optional: Wait 1 second so user sees the message, then redirect
        #                 import time
        #                 time.sleep(1)
        #                 st.session_state.current_view = "dashboard"
        #                 st.rerun()
        #             else:
        #                 # Show the exact error from FastAPI
        #                 error_detail = res.json().get("detail", "Unknown Error")
        #                 st.error(f"Failed to create character: {error_detail}")
        #         except Exception as e:
        #             st.error(f"Connection Error: {e}")
        if submitted:
            # 1. Define what fields MUST be filled
            required_fields = {
                "Unique ID": char_id,
                "Name": name,
                "Role": role,
                "Personality": personality,
                "Backstory": backstory,
                "Speaking Style": style
            }
            
            # 2. Check for missing values
            missing = [key for key, value in required_fields.items() if not value.strip()]
            
            if missing:
                # Show exactly what is missing
                st.error(f"⚠️ Please fill in the following required fields: {', '.join(missing)}")
            
            else:
                # 3. If all good, proceed with payload
                payload = {
                    "char_id": char_id.lower().strip(),
                    "name": name,
                    "prompt_data": {
                        "CHAR_NAME": name,
                        "CHAR_ROLE": role,
                        "CHAR_AGE": age or "Unknown", # Optional: Provide defaults for non-critical fields
                        "CHAR_APPEARANCE": appearance or "Not specified",
                        "CHAR_PERSONALITY": personality,
                        "CHAR_BACKSTORY": backstory,
                        "SPEAKING_STYLE": style,
                        "CHAR_QUIRKS": quirks or "None",
                        "CHAR_TONE": tone or "Neutral",
                        "CURRENT_SETTING": setting or "A void",
                        "USER_RELATIONSHIP": rel or "Stranger",
                        "CHAR_GOAL": goal or "To exist"
                    }
                }
                
                try:
                    res = requests.post(f"{API_URL}/create-character", json=payload, headers=get_headers())
                    
                    if res.status_code == 200:
                        st.success(f"🎉 Character '{name}' created successfully!")
                        import time
                        time.sleep(1)
                        st.session_state.current_view = "dashboard"
                        st.rerun()
                    else:
                        error_detail = res.json().get("detail", "Unknown Error")
                        st.error(f"Failed to create character: {error_detail}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")


# --- CHAT INTERFACE ---
elif st.session_state.current_view == "chat":
    char = st.session_state.selected_char
    st.button("← Back", on_click=lambda: st.session_state.update({"current_view": "dashboard"}))
    st.title(char['name'])

    # 1. GENERATE UNIQUE KEY FOR THIS CHAT SESSION
    # This ensures Max's Mario chat is stored separately from Jenil's Mario chat in RAM
    # Key format: "chat_max_mario" or "chat_guest_mario"
    session_key = f"chat_{st.session_state.username}_{char['id']}"

    # 2. FETCH HISTORY IF NOT LOADED
    if session_key not in st.session_state:
        # Load from DB
        raw_history = fetch_chat_history(char['id'])
        formatted_history = []
        for msg in raw_history:
            # Backend sends "type": "human" or "ai". Streamlit needs "role": "user" or "assistant"
            role = "user" if msg.get("type") == "human" else "assistant"
            formatted_history.append({"role": role, "content": msg.get("content")})
        st.session_state[session_key] = formatted_history

    # 3. DISPLAY MESSAGES
    for msg in st.session_state[session_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 4. HANDLE INPUT
    if prompt := st.chat_input():
        # Append User Msg locally
        st.session_state[session_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Send to API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    res = requests.post(
                        f"{API_URL}/chat/{char['id']}/1",
                        json={"messages": prompt},
                        headers=get_headers()
                    )
                    if res.status_code == 200:
                        reply = res.json()
                        st.markdown(reply)
                        st.session_state[session_key].append({"role": "assistant", "content": reply})
                    else:
                        st.error("API Error")
                except Exception as e:
                    st.error(f"Connection Error: {e}")