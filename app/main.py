import streamlit as st
import base64
from dotenv import load_dotenv
from openai import OpenAI
import os
from utils import add_message, ai_resposne, read_random_info, random_GNR

st.set_page_config(page_title="Natalino", layout="wide")

load_dotenv(".env.dev")

def reload_page():
    st.rerun()

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
        print("File read as binary")
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }

    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)
def add_custom_css():
    st.markdown(
        """
        <style>
        .stChatInput {
            position: fixed;
            bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Aggiungi il CSS personalizzato
add_custom_css()
set_background('./static/background.jpg')
st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        .stAppHeader {display: none;}
        .stMainBlockContainer{padding-top: 10px;}
    </style>
""", unsafe_allow_html=True)

### Initial setup when loading chat ###
# Initialize chat history
if "messages" not in st.session_state:
    initial_prompt = open("context_information.txt", "r").read()
    st.session_state.messages = [{"role": "system", "content": initial_prompt}]
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI(
    )
if "random_info" not in st.session_state:
    st.session_state.random_info = read_random_info()["list"]


c1, c2 = st.columns([1,2])

with c1:
    if st.button("Nuova chat"):
        initial_prompt = open("context_information.txt", "r").read()
        st.session_state.messages = [{"role": "system", "content": initial_prompt}]
        reload_page()
    st.title("Natalino")

with c2:
    if len(st.session_state.messages) != 1:
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
    else:

        #left, right = st.columns(2)
        #n = 4 # Number of random info
        #r = random_GNR(n)
        #for i in range(n//2):
        #    i = next(r)
        #   if left.button(st.session_state.random_info[i], use_container_width=True, key=f'left_button{i}'):
        #        add_message("user", st.session_state.random_info[i])
        #        reload_page()
        #    i = next(r)
        #    if right.button(st.session_state.random_info[i], use_container_width=True, key=f'left_button{i}'):
        #        add_message("user", st.session_state.random_info[i])
        #        reload_page()

        st.markdown("<p style='color: #D9D9D9; font-size: 30px;'>Ciao, sono Natalino!</p>", unsafe_allow_html=True)
        st.markdown("<p style='color: #D9D9D9; font-size: 30px;'>Chiedimi ciò che vuoi sul Presepio Meccanico!</p>", unsafe_allow_html=True)


    if user_input := st.chat_input("Scrivi qui"):
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
        reload_page()
