import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import os
from utils import add_message, ai_resposne, read_random_info, random_GNR

load_dotenv(".env.dev")

def reload_page():
    st.rerun()

### Initial setup when loading chat ###
# Initialize chat history
if "messages" not in st.session_state:
    initial_prompt = open("context_information.txt", "r").read()
    st.session_state.messages = [{"role": "system", "content": initial_prompt}]
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI(
    )

# Page
st.title("Natalino")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "random_info" not in st.session_state:
    st.session_state.random_info = read_random_info()["list"]

if len(st.session_state.messages) == 1:
    left, right = st.columns(2)
    n = 4 # Number of random info
    r = random_GNR(n)
    for i in range(n//2):
        i = next(r)
        if left.button(st.session_state.random_info[i], use_container_width=True, key=f'left_button{i}'):
            add_message("user", st.session_state.random_info[i])
            reload_page()
        i = next(r)
        if right.button(st.session_state.random_info[i], use_container_width=True, key=f'left_button{i}'):
            add_message("user", st.session_state.random_info[i])
            reload_page()
else:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            stream_response = ai_resposne(st.session_state.messages, st.session_state.openai_client)
            response = st.write_stream(stream_response)
            # Add assistant response to chat history
        add_message("assistant", response)

# Accept user input
if user_input := st.chat_input("What is up?"):
    # Add user message to chat history
    add_message("user", user_input)
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(user_input)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        stream_response = ai_resposne(st.session_state.messages, st.session_state.openai_client)
        response = st.write_stream(stream_response)
        # Add assistant response to chat history
    add_message("assistant", response)
