import streamlit as st
from datetime import datetime
import uuid
from run import call_my_model
from my_local_db import add_message,get_thread_messages,load_history,save_history,get_all_users,get_latest_thread_for_user

# ---------- Initialization ----------
if "threads" not in st.session_state:
    st.session_state.threads = load_history()

if "all_threads" not in st.session_state:
    st.session_state.all_current_user_threads = None

if "active_thread" not in st.session_state:
    st.session_state.active_thread = None

if "models" not in st.session_state:
    st.session_state.models = ["GPT-4", "GPT-3.5", "Mistral", "Custom"]

if "tools" not in st.session_state:
    st.session_state.tools = ["Code Interpreter", "Web Browser", "DALL-E"]

if "all_users" not in st.session_state:
    st.session_state.users = get_all_users()

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ---------- Sidebar UI ----------
st.sidebar.title("💬 ChatGPT Clone")

select_user = st.sidebar.selectbox(
    "Select user name",
    options=["+ newuser"] + st.session_state.users ,
)

if select_user =="+ newuser":
    name=st.sidebar.text_input("enter new user name: ")
    create_user=st.sidebar.button("create user")
    if name and create_user:
        st.session_state.current_user = name
        data=load_history()
        data[name]={}
        save_history(data)
else:
    st.session_state.current_user = select_user
    

latest_thread,all_current_user_threads=get_latest_thread_for_user(load_history(),st.session_state.current_user)

if latest_thread is not None:
    st.session_state.active_thread=latest_thread

if len(all_current_user_threads)>0:
    st.session_state.all_current_user_threads = all_current_user_threads

if st.session_state.current_user is not None:
    selected_thread = st.sidebar.selectbox(
        "Select a conversation",
        options=["+ New Thread"] + all_current_user_threads) 
    
        # If an existing thread is selected, set active_thread
    if selected_thread != "+ New Thread":
        st.session_state.active_thread = selected_thread
else:
    st.sidebar.markdown("please create or select user")

uploaded_files = st.sidebar.file_uploader("Upload files", accept_multiple_files=True)
if uploaded_files:
    st.sidebar.success(f"Uploaded {len(uploaded_files)} file(s)")

selected_model = st.sidebar.selectbox("Choose model", st.session_state.models)
selected_tools = st.sidebar.multiselect("Enable tools", st.session_state.tools)

st.sidebar.markdown("### 🎙️ Record Message (Simulated)")
if st.sidebar.button("Record"):
    st.sidebar.info("Recording... (simulated)")

# ---------- Main Chat Area ----------
st.title("🧠 ChatGPT-Like UI")


try:
# Show chat history if active thread exists
    if st.session_state.active_thread and st.session_state.active_thread in st.session_state.all_current_user_threads:
        history = st.session_state.threads[st.session_state.current_user][st.session_state.active_thread]
        for entry in history:
            with st.chat_message(entry["role"]):
                st.markdown(entry["message"])
except:
    st.markdown("no user histry")
# User input
user_input = st.chat_input("Send a message")

if user_input:
    # If new thread, create only now
    if selected_thread == "+ New Thread":
        thread_id = str(uuid.uuid4())[:8]
        st.session_state.threads[st.session_state.current_user][thread_id] = []
        st.session_state.active_thread = thread_id
    else:
        thread_id = st.session_state.active_thread

    # Add user message
    st.session_state.threads[st.session_state.current_user][thread_id].append({
        "role": "user",
        "message": user_input,
        "timestamp": datetime.now().isoformat()
    })

    add_message(st.session_state.current_user,thread_id,"user",user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call model for response
    model_output = call_my_model(user_input)

    # Add assistant message
    st.session_state.threads[st.session_state.current_user][thread_id].append({
        "role": "assistant",
        "message": model_output,
        "timestamp": datetime.now().isoformat()
    })
    add_message(st.session_state.current_user,thread_id,"assistant",model_output)

    with st.chat_message("assistant"):
        st.markdown(model_output)

    st.rerun()
