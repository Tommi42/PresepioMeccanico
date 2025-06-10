import streamlit as st
from streamlit_lottie import st_lottie
import base64
import time
from dotenv import load_dotenv
from openai import OpenAI
import os
import random

from utils import add_message, ai_resposne, read_random_info, random_GNR
from pip._vendor.requests import delete

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
        .stCustomComponentV1{
            background-color: #D9D9D9;
            border-radius: 100px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )
def set_chat_input_width(width):
    st.markdown(
        """
        <style>
        div[data-testid="stChatInput"] {
            display: flex;
            justify-content: center;
        }
        div[data-testid="stChatInput"] > div {
            width: """ + str(width) + """px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
def delete_header():
    st.markdown("""
        <style>
            .reportview-container {
                margin-top: -2em;
            }
            .stAppHeader {display: none;}
            .stMainBlockContainer{padding-top: 10px;}
        </style>
    """, unsafe_allow_html=True)



#add_custom_css()
set_chat_input_width(900)
set_background('./static/background.jpg')
delete_header()


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
    random.shuffle(st.session_state.random_info)


def menage_message(input):
    # Add user message to chat history
    user_input = input
    add_message("user", user_input)
    reload_page()

    # Display assistant response in chat message container
    with messages.chat_message("assistant"):
        stream_response = ai_resposne(st.session_state.messages, st.session_state.openai_client)
        response = st.write_stream(stream_response)
        # Add assistant response to chat history
    add_message("assistant", response)

n_random = len(st.session_state.random_info)

c1, c2 = st.columns([1,3])

with c1:
    if st.button("Nuova chat"):
        initial_prompt = open("context_information.txt", "r").read()
        st.session_state.messages = [{"role": "system", "content": initial_prompt}]
        reload_page()
    st.title("Natalino")
    st.image("./static/Natalino.png", width=130)

with c2:
    messages = st.container(border=False, height=600)
    if len(st.session_state.messages) != 1:
        print(len(st.session_state.messages))
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            if message["role"] != "system":
                with messages.chat_message(message["role"]):
                    st.markdown(message["content"])

        if st.session_state.messages[-1]["role"] == "user":
            with messages.chat_message("assistant"):
                stream_response = ai_resposne(st.session_state.messages, st.session_state.openai_client)
                response = st.write_stream(stream_response)
                # Add assistant response to chat history
            add_message("assistant", response)
    else:
        messages.markdown("<p style='color: #FFFFFF; font-size: 30px;'>Chiedimi ciò che vuoi sul Presepio Meccanico!</p>", unsafe_allow_html=True)

        grid_c1, grid_c2 = messages.columns([1,1])

        if grid_c1.button(st.session_state.random_info[0], use_container_width=True):
            menage_message(st.session_state.random_info[0])
        elif grid_c1.button(st.session_state.random_info[1], use_container_width=True):
            menage_message(st.session_state.random_info[1])
        elif grid_c2.button(st.session_state.random_info[2], use_container_width=True):
            menage_message(st.session_state.random_info[2])
        elif grid_c2.button(st.session_state.random_info[3], use_container_width=True):
            menage_message(st.session_state.random_info[3])

    if user_input := st.chat_input("Scrivi qui"):
        menage_message(user_input)
