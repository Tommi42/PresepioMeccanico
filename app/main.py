import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import os
from utils import add_message, ai_resposne

load_dotenv(".env.dev")

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

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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
