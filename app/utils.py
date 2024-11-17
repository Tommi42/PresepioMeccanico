import streamlit as st
import json
import random

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})


def ai_resposne(messages, openai_client):
     stream_response = openai_client.chat.completions.create(
         model="gpt-4o-mini",
         messages=messages,
         stream=True
     )
     return stream_response

def read_random_info():
    with open("random_info.json", "r") as file:
        return json.load(file)

def random_GNR(n):
    l = list(range(0, n, 1))
    random.shuffle(l)
    for i in l:
        yield i
