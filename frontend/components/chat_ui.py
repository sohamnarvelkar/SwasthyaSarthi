import streamlit as st

def display_chat(history):
    """
    Displays chat history as markdown.
    Input: history is a list of (speaker, message) tuples.
    """
    for speaker, message in history:
        if speaker == "You":
            st.markdown(f"**You:** {message}")
        else:
            st.markdown(f"**SwasthyaSarthi:** {message}")
