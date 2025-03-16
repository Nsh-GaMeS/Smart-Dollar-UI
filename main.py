import streamlit as st
import time
import requests

API_BASE_URL = "http://127.0.0.1:9000"  # Replace with your actual API URL

# --- Splash Screen ---
def splash_screen():
    st.markdown("""
        <h1 style='text-align: center;'>💰 Finance Tracker</h1>
        <p style='text-align: center;'>Loading your personal finance dashboard...</p>
    """, unsafe_allow_html=True)
    
    with st.spinner("Starting up..."):
        time.sleep(2)  # Simulating a loading delay
    st.session_state["page"] = "login"
    st.rerun()

# --- Login Page ---
def login_page():
    st.title("🔑 Login")
    
    # Collect user credentials
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Login"):
            # Send the login request
            response = requests.post(
                f"{API_BASE_URL}/auth/login", 
                json={
                    "username": username, 
                    "password": password
                    })
            
            if response.status_code == 200:
                user_data = response.json()
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = str(user_data["id"])  # Store user ID in session state
                st.session_state["page"] = "home"
                st.rerun()
            else:
                st.error("Invalid credentials. Try again.")

    with col2:
        if st.button("Sign Up"):
            st.session_state["page"] = "signup"
            st.rerun()

# --- Sign Up Page ---
def signup_page():
    st.title("📝 Create an Account")

    # Collect user data, username, password, and email
    new_email = st.text_input("Email Address (optional)")
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        # Validate password match
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            # Send the registration request
            response = requests.post(
                f"{API_BASE_URL}/auth/register",
                json={
                    "email": new_email,
                    "username": new_username, 
                    "password": new_password
                    })
            
            if response.status_code == 200:
                st.success("Account created successfully! Please log in.")
                st.session_state["page"] = "login"
                st.rerun()
            else:
                st.error("Sign up failed. Try a different username.")

# --- Home Page ---
def home_page():
    st.title("🏠 Finance Dashboard")
    st.write("Welcome to your personal finance tracker!")

    # Fetch and display accounts
    response = requests.get(
        f"{API_BASE_URL}/auth/get_accounts",
        params={"user_id": st.session_state['user_id']}
    )
    
    if response.status_code == 200:
        accounts = response.json()
        st.write("💰 Your Savings Goals:")

        for account in accounts:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 1])

                with col1:
                    open_button = st.button(f"{account['name']}", key=f"open_{account['id']}")
                    st.write(f"🎯 Goal: ${account['final_goal']}" if account["final_goal"] else "🎯 Goal: Not Set")
                    st.write(f"⏳ Time Frame: {account['time_frame']}" if account["time_frame"] else "⏳ Time Frame: Not Set")

                with col2:
                    st.write(f"💰 Balance: ${account['curr_balance']}")

                  # Ensure session state is initialized before using it
                if f"add_{account['id']}" not in st.session_state:
                    st.session_state[f"add_{account['id']}"] = 0.0
                if f"withdraw_{account['id']}" not in st.session_state:
                    st.session_state[f"withdraw_{account['id']}"] = 0.0
                    
                with col3:
                    add_amount = st.number_input(f"Deposite to {account['name']}", min_value=0.0, step=0.01, key=f"add_{account['id']}")
                    add_button = st.button("➕", key=f"add_button_{account['id']}")
                    

                with col4:
                    if f"withdraw_{account['id']}" not in st.session_state:
                        st.session_state[f"withdraw_{account['id']}"] = 0.0
                    withdraw_amount = st.number_input(f"Withdraw from {account['name']}", min_value=0.0, step=0.01, key=f"withdraw_{account['id']}")
                    withdraw_button = st.button("➖", key=f"withdraw_button_{account['id']}")

                with col5:
                    delete_button = st.button("❌", key=f"delete_{account['id']}")

                if open_button:
                    st.session_state["page"] = "account_details"
                    st.session_state["selected_account"] = account["id"]
                    st.rerun()

                if add_button:
                    if add_amount <= 0:
                        st.error("Please enter a valid amount to add.")
                        st.stop()
                    new_balance = account['curr_balance'] + add_amount
                    response = requests.get(
                        f"{API_BASE_URL}/auth/update_account_balance",
                        params={"account_id": account['id'], "new_balance": new_balance}
                    )
                    if response.status_code == 200:
                        st.success("Balance updated successfully!")
                        if new_balance >= account['final_goal']:
                            st.success("Goal met!")
                    else:
                        st.error("Failed to update balance.")

                    payload = {
                            "amount": add_amount,
                            "user_id": st.session_state['user_id'],
                        }
                    response = requests.post(
                        f"{API_BASE_URL}/auth/add_transaction",
                        json=payload
                    )
                    if response.status_code == 200:
                        st.success("Transaction recorded successfully!")
                    else:
                        st.error("Failed to record transaction.")

                     # **Reset deposit input field before reloading**
                    st.session_state.pop(f"add_{account['id']}", None)     
                    st.rerun()

                if withdraw_button:
                    if withdraw_amount <= 0 or withdraw_amount > account['curr_balance']:
                        st.error("Please enter a valid amount to withdraw.")
                        st.stop()
                    new_balance = account['curr_balance'] - withdraw_amount
                    response = requests.get(
                        f"{API_BASE_URL}/auth/update_account_balance",
                        params={"account_id": account['id'], "new_balance": new_balance}
                    )
                    if response.status_code == 200:
                        st.success("Balance updated successfully!")
                    else:
                        st.error("Failed to update balance.")

                    payload = {
                            "amount": -withdraw_amount,
                            "user_id": st.session_state['user_id'],
                        }
                    response = requests.post(
                        f"{API_BASE_URL}/auth/add_transaction",
                        json=payload
                    )
                    if response.status_code == 200:
                        st.success("Transaction recorded successfully!")
                    else:
                        st.error("Failed to record transaction.")
                    st.rerun()

                if delete_button:
                    response = requests.get(
                        f"{API_BASE_URL}/auth/delete_account/", 
                        params={"account_id": account['id']}
                    )
                    if response.status_code == 200:
                        st.success("Account deleted successfully!")
                    else:
                        st.error("Failed to delete account.")
                    
                    # **Reset withdrawal input field before reloading**
                    st.session_state.pop(f"withdraw_{account['id']}", None)
                    st.rerun()

    # Navigation to Create New Account Page
    if st.button("➕ Create New Account"):
        st.session_state["page"] = "create_account"
        st.rerun()

    # AI suggestion
    if st.button("🤖 AI Suggestion"):
        response = requests.get(
            f"{API_BASE_URL}/gemini/analyze_spending",
            params={"user_id": st.session_state['user_id']}
            )
        if response.status_code == 200:
            suggestion = response.json()
            st.write("Dollar AI Suggestion:")
            for value in suggestion.values():
                st.write(value)
        else:
            st.error("Failed to get AI suggestion.")

# --- Create New Account Page ---
def create_account_page():
    st.title("➕ Create a New Savings Goal")

    new_name = st.text_input("Account Name")
    new_balance = st.number_input("Initial Balance", min_value=0.0, step=0.01)
    new_goal = st.number_input("Final Goal (optional)", min_value=0.0, step=0.01)
    new_time_frame = st.date_input("Time Frame (optional)")
    new_interest = st.number_input("Interest Rate (optional, %)", min_value=0.0, step=0.01)
    new_fees = st.number_input("Fees (optional)", min_value=0.0, step=0.01)

    if st.button("Create Account"):
        payload = {
            "name": new_name,
            "curr_balance": new_balance,
            "final_goal": new_goal if new_goal > 0 else None,
            "time_frame": str(new_time_frame) if new_time_frame else None,
            "interest_rate": new_interest if new_interest > 0 else None,
            "fees": new_fees if new_fees > 0 else None,
        }
        response = requests.post(f"{API_BASE_URL}/auth/add_account", params={"user_id": st.session_state['user_id']}, json=payload)

        if response.status_code == 200:
            st.success("Account created successfully!")
            st.session_state["page"] = "home"
            st.rerun()
        else:
            st.error("Failed to create account.")

    if st.button("⬅ Back to Home"):
        st.session_state["page"] = "home"
        st.rerun()

# --- Account Details Page ---
def account_details():
    st.title("📄 Account Details")

    account_id = st.session_state.get("selected_account")
    if not account_id:
        st.error("No account selected!")
        return

    response = requests.get(
        f"{API_BASE_URL}/auth/get_account_details/", 
        params={"account_id": account_id}
        )
    
    if response.status_code == 200:
        account = response.json()
        st.write(f"### {account['name']}")
        st.write(f"💰 **Current Balance:** ${account['curr_balance']}")
        st.write(f"🎯 **Final Goal:** ${account['final_goal']}" if account["final_goal"] else "🎯 **Final Goal:** Not Set")
        st.write(f"⏳ **Time Frame:** {account['time_frame']}" if account["time_frame"] else "⏳ **Time Frame:** Not Set")
        st.write(f"📈 **Interest Rate:** {account['interest_rate']}%" if account["interest_rate"] else "📈 **Interest Rate:** Not Set")
        st.write(f"💸 **Fees:** ${account['fees']}" if account["fees"] else "💸 **Fees:** Not Set")

        with st.form(key="back_to_home_form"):
            if st.form_submit_button("Back to Home"):
                st.session_state["page"] = "home"
                st.rerun()
    else:
        st.error("Error fetching account details.")

# --- Page Router ---
if "page" not in st.session_state:
    splash_screen()
elif st.session_state["page"] == "login":
    login_page()
elif st.session_state["page"] == "signup":
    signup_page()
elif st.session_state["page"] == "account_details":
    account_details()
elif st.session_state["page"] == "create_account":
    create_account_page()   
elif st.session_state.get("logged_in"):
    home_page()
else:
    login_page()
