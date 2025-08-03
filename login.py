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

def create_user(username: str, password: str):
    # Check if user already exists
    if db.get_user_by_name(username.lower()):
        return False
    hashed_pw = hash_password(password)
    db.add_user(username.lower(), hashed_pw)  # <-- Ensure this method exists in your Database class
    return True

def register_form():
    st.subheader("📝 Register")
    username = st.text_input("Choose a username", key="reg_user")
    password = st.text_input("Choose a password", type="password", key="reg_pass")
    confirm_password = st.text_input("Confirm password", type="password", key="reg_confirm")
    
    if st.button("Register", use_container_width=True, key="register_btn"):
        if password != confirm_password:
            st.error("❌ Passwords do not match")
        elif not username or not password:
            st.error("❌ Username and password cannot be empty")
        elif create_user(username, password):
            st.success("✅ Registration successful! Please log in.")
            st.session_state.show_register = False
            st.rerun()
        else:
            st.error("❌ Username already exists")
    if st.button("Back to login", use_container_width=True, key="back_to_login"):
        st.session_state.show_register = False
        st.rerun()

def login_form():
    st.subheader("🔐 Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", use_container_width=True, key="login_btn"):
        if check_credentials(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username.lower()
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    if st.button("Create an account", use_container_width=True, key="to_register"):
        st.session_state.show_register = True
        st.rerun()

def login():
    st.title("🛡️ Authentication")
    if "show_register" not in st.session_state:
        st.session_state.show_register = False

    if st.session_state.show_register:
        register_form()
    else:
        login_form()

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
