import streamlit as st

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})


def ai_resposne(messages, openai_client):
     stream_response = openai_client.chat.completions.create(
         model="gpt-4o-mini",
         messages=messages,
         stream=True
     )
     return stream_response
