"""Shared local authentication service; patient/case state stays session-scoped."""
import streamlit as st

from medical_assistant.auth import LocalAuth
from medical_assistant.database import DATABASE_PATH, seed


@st.cache_resource
def get_services():
    seed(DATABASE_PATH)
    return DATABASE_PATH, LocalAuth(DATABASE_PATH)
