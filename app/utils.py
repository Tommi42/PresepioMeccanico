from numpy import prod
import streamlit as st
import json
import random
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv(".env.dev")
client = OpenAI()

def message_streamer(messages,run):
    response = ''
    try:
        for event in run:

            try:
                if event.event == "thread.message.delta":
                    response += str(event.data.delta.content[0].text.value)
                    yield str(event.data.delta.content[0].text.value)
            except:
                pass

    finally:
        messages.append({'role': 'assistant', 'content': response})

def add_message(messages, role, content):
    thread_message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread.id,
        role=role,
        content=content
    )
    messages.append({'role': role, 'content': content})

def ai_resposne(messages, openai_client):
     run = client.beta.threads.runs.create(
       thread_id=st.session_state.thread.id,
       assistant_id=str(os.environ["ASSISTANT_ID"]),
       stream=True
     )
     return message_streamer(messages, run)

def read_random_info():
    with open("random_info.json", "r") as file:
        return json.load(file)

def random_GNR(n):
    l = list(range(0, n, 1))
    random.shuffle(l)
    for i in l:
        yield i

def create_thread():
    thread = client.beta.threads.create()
    return thread
