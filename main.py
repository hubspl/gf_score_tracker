import streamlit as st
from god import app as score_input_app
from history import app as game_history_app

pages = {
    "Game History": game_history_app,
    "Add Game": score_input_app    
}

# Initialize session_state for page if not set
if "page" not in st.session_state:
    st.session_state.page = "Game History"

st.sidebar.title("Godfather")

# Show all pages as buttons
for page_name in pages:
    if st.sidebar.button(page_name):
        st.session_state.page = page_name

# Run the selected page function
pages[st.session_state.page]()