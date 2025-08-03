# auth.py
import streamlit as st
import hashlib

from database import Database
# Load data
db = Database()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username : str, password):
    user = db.get_user_by_name(username.lower())
    print(user)
    print(username,hash_password(password))
    if user is None:
        return False
    return user.password == hash_password(password)

def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if check_credentials(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username.lower()
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

def logout():
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

def require_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        login()
        st.stop()

    # Show logout in sidebar once logged in
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    logout()
