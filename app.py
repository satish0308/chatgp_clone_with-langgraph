import streamlit as st
from datetime import datetime
import uuid
from run import get_check_points
from my_local_db import add_message,get_thread_messages,load_history,save_history,get_all_users,get_latest_thread_for_user
from langchain_core.messages import AnyMessage,HumanMessage

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
    options=["+ newuser"] + st.session_state.users ,)
    # index=len(st.session_state.users)-1 if len(st.session_state.users) > 1 else 0)

if select_user =="+ newuser":
    name=st.sidebar.text_input("enter new user name: ")
    create_user=st.sidebar.button("create user")
    if name and create_user:
        st.session_state.current_user = name
        data=load_history()
        data[name]={}
        save_history(data)
    st.session_state.active_thread=None
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
        options=["+ New Thread"] + all_current_user_threads,)
        # index=len(all_current_user_threads)-1 if len(all_current_user_threads) > 1 else 0) 
    
        # If an existing thread is selected, set active_thread
    if selected_thread != "+ New Thread":
        st.session_state.active_thread = selected_thread
    else:
        st.sidebar.markdown("New Thread will Get Created")
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

st.write(f"**User:** `{st.session_state.current_user}` | **Thread:** `{st.session_state.active_thread}`")

if user_input:


    # If new thread, create only now
    if selected_thread == "+ New Thread":
        thread_id = str(uuid.uuid4())[:8]
        st.session_state.threads = load_history()
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
    # model_output = call_my_model(user_input,st.session_state.active_thread)

    config = {"configurable": {"thread_id": thread_id}}
    placeholder = st.empty()
    streamed_text = ""

    # Only call get_check_points and store in session_state if not already stored
    if "build" not in st.session_state or "checkpointer" not in st.session_state or "context" not in st.session_state:
        build, checkpointer, context = get_check_points()
        st.session_state.build = build
        st.session_state.checkpointer = checkpointer
        st.session_state.context = context
    else:
        build = st.session_state.build
        checkpointer = st.session_state.checkpointer
        context = st.session_state.context

    for chunk in build.stream(
        {"input": [HumanMessage(user_input)]},
        config,
        context=context,
        stream_mode="updates",resume=True
    ):
        # Extract the latest chunk's text
        text_piece = chunk["call_llm"]["input"][-1].content
        streamed_text += text_piece
        placeholder.markdown(streamed_text)

    print(config)
    print(user_input)
    print(streamed_text)

    # Add assistant message
    st.session_state.threads[st.session_state.current_user][thread_id].append({
        "role": "assistant",
        "message": streamed_text,
        "timestamp": datetime.now().isoformat()
    })
    add_message(st.session_state.current_user,thread_id,"assistant",streamed_text)

    with st.chat_message("assistant"):
        st.markdown(streamed_text)

    st.rerun()
