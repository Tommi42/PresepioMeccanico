import base64
import os
import time

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pip._vendor.requests import delete
from streamlit_lottie import st_lottie
from utils import add_message, ai_resposne, random_GNR, read_random_info

st.set_page_config(page_title="Natalino", layout="wide")
openai_api_key = os.getenv("OPENAI_API_KEY")


print("Nuovo Timer")
timer = time.time()


def reload_page():
    st.rerun()


def get_base64(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
        print("File read as binary")
    return base64.b64encode(data).decode()


def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = (
        """
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }

    </style>
    """
        % bin_str
    )
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
        unsafe_allow_html=True,
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
            width: """
        + str(width)
        + """px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def delete_header():
    st.markdown(
        """
        <style>
            .reportview-container {
                margin-top: -2em;
            }
            .stAppHeader {display: none;}
            .stMainBlockContainer{padding-top: 10px;}
        </style>
    """,
        unsafe_allow_html=True,
    )


def set_chat_input_full_width():
    st.markdown(
        """
            <style>
            div[data-testid="stChatInput"] {
                width: 100vw !important;
                max-width: 100vw !important;
                left: 0;
                right: 0;
                margin: 0 auto;
            }
            </style>
            """,
        unsafe_allow_html=True,
    )


def set_chat_input_c2_width():
    st.markdown(
        """
        <style>
        div[data-testid="stChatInput"] {
            width: 40vw !important;   /* Circa 2/5 della pagina */
            max-width: 40vw !important;
            margin-left: auto;
            margin-right: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_title_yellow():
    st.markdown(
        """
        <style>
        h1 {
            color: #FFD600 !important; /* Giallo acceso */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    /* Forza il colore bianco nei messaggi della chat */
    .stChatMessageContent, .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: #fff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


add_custom_css()
set_background("./app/static/Sfondo05.png")
set_chat_input_c2_width()
delete_header()
set_title_yellow()
# Inietta JavaScript
st.markdown(
    """
<script>
document.addEventListener('click', function(e) {
  const link = e.target.closest('a');
  if (link) {
      alert("Navigazione esterna non consentita!");
  }
});
</script>
""",
    unsafe_allow_html=True,
)


### Initial setup when loading chat ###
# Initialize chat history
if "messages" not in st.session_state:
    initial_prompt = open("app/context_information.txt", "r").read()
    st.session_state.messages = [{"role": "system", "content": initial_prompt}]
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI()
if "random_info" not in st.session_state:
    st.session_state.random_info = read_random_info()["list"]


c1, c2 = st.columns([3, 2])

user_input = c2.chat_input(placeholder="Scrivi qui")


with c1:
    v1, v2 = st.columns([1, 2])

    with v1:
        st.container(width="stretch", height=100, border=False)
        st.title("Natalino")
        st.image("./app/static/Natalino02.png", width=250)

    with v2:
        st.container(width="stretch", height=100, border=False)
        if user_input:
            # Add user message to chat history
            add_message("user", user_input)
            # Display assistant response in chat message container
            with st.chat_message("natalino", avatar=":)"):
                stream_response = ai_resposne(
                    st.session_state.messages, st.session_state.openai_client
                )
                response = st.write_stream(stream_response)
                # Add assistant response to chat history
            add_message("assistant", response)

with c2:
    st.title("Ciao sono Natalino!")
    st.subheader("Sono qui per aiutarti a scoprire tutto su Presepio Meccanico!")
    st.container(width="stretch", height=200, border=False)
    st.image("./app/static/Falegnami03.png", width=500)

    # st.markdown("<p style='color: #D9D9D9; font-size: 30px;'>Ciao, sono Natalino!</p>", unsafe_allow_html=True)
    # st.markdown("<p style='color: #D9D9D9; font-size: 30px;'>Chiedimi ciò che vuoi sul Presepio Meccanico!</p>", unsafe_allow_html=True)
