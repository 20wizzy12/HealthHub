import streamlit as st
import json
import os
import hashlib
import datetime
import pandas as pd

# --------- UTILS ----------
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --------- APP ----------
st.set_page_config(page_title="Health App", page_icon="💪", layout="centered")

st.title("💪 Health & Wellness App")

users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- AUTO LOGIN CHECK ---
remembered_user = None
for u, data in users.items():
    if data.get("remember", False):
        remembered_user = u
        break

if remembered_user and not st.session_state.logged_in:
    st.session_state.logged_in = True
    st.session_state.username = remembered_user

# SIGN UP + LOGIN
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab2:
        st.subheader("Create a new account")
        new_user = st.text_input("Username", key="signup_user")
        new_pass = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Sign Up"):
            if new_user in users:
                st.error("🚨 Username already exists, pick another!")
            elif new_user.strip() == "" or new_pass.strip() == "":
                st.warning("⚠️ Username and password cannot be empty")
            else:
                users[new_user] = {
                    "password": hash_password(new_pass),
                    "data": {"weight": 0.0, "height": 0, "calories": 2000, "water": 8, "exercise": 30},
                    "history": [],
                    "remember": False
                }
                save_users(users)
                st.success("✅ Account created! You can now log in.")

    with tab1:
        st.subheader("Login to your account")
        user = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        remember_me = st.checkbox("Remember Me")

        if st.button("Login"):
            if user in users and users[user]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.username = user

                # reset all others
                for u in users:
                    users[u]["remember"] = False
                # set this user as remembered
                users[user]["remember"] = remember_me
                save_users(users)

                st.success(f"🎉 Welcome back, {user}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

# MAIN APP (after login)
if st.session_state.logged_in:
    username = st.session_state.username
    st.sidebar.success(f"Logged in as {username}")
    if st.sidebar.button("Logout"):
        # disable remember flag
        users[username]["remember"] = False
        save_users(users)

        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Load user data
    user_data = users[username]["data"]

    st.subheader("🩺 Health Check")

    weight = st.number_input(
        "Enter your weight (kg):",
        min_value=1.0,
        value=max(1.0, float(user_data.get("weight", 70.0))),  
        step=0.1
    )


    height = st.number_input(
        "Enter your height (cm):",
        min_value=50,
        value=max(50, int(user_data.get("height", 170))),  # safe default of 170
        step=1,
        format="%d"
)



    if st.button("Calculate BMI"):
        if height > 0:
            bmi = weight / ((height / 100) ** 2)
            st.success(f"Your BMI is **{bmi:.2f}**")
            if bmi < 18.5:
                st.warning("⚠️ Underweight: You might need more nutrition.")
            elif 18.5 <= bmi < 24.9:
                st.info("✅ Normal: Keep it up!")
            elif 25 <= bmi < 29.9:
                st.warning("⚠️ Overweight: Consider some lifestyle changes.")
            else:
                st.error("🚨 Obese: Consult a doctor or nutritionist.")

            users[username]["data"]["weight"] = weight
            users[username]["data"]["height"] = height
            save_users(users)
        else:
            st.error("Height must be greater than 0 to calculate BMI.")

    st.subheader("🥗 Daily Health Tracker")
    calories = st.slider("Calories consumed today:", 0, 5000, user_data.get("calories", 2000))
    water = st.slider("Glasses of water today:", 0, 20, user_data.get("water", 8))
    exercise = st.slider("Minutes of exercise today:", 0, 300, user_data.get("exercise", 30))

    st.write(f"🔥 Calories: {calories} kcal")
    st.write(f"💧 Water intake: {water} glasses")
    st.write(f"🏃 Exercise: {exercise} mins")

    if st.button("💾 Save Progress"):
        bmi = weight / ((height / 100) ** 2) if height > 0 else 0

        users[username]["data"]["weight"] = weight
        users[username]["data"]["height"] = height
        users[username]["data"]["calories"] = calories
        users[username]["data"]["water"] = water
        users[username]["data"]["exercise"] = exercise

        users[username].setdefault("history", [])
        users[username]["history"].append({
            "date": str(datetime.date.today()),
            "bmi": round(bmi, 2),
            "calories": calories,
            "water": water,
            "exercise": exercise
        })

        save_users(users)
        st.success("✅ Progress saved successfully!")

    if "history" in users[username] and len(users[username]["history"]) > 0:
        st.subheader("📊 Your Progress Over Time")

        df = pd.DataFrame(users[username]["history"])
        st.line_chart(df.set_index("date")[["bmi", "calories", "water", "exercise"]])
        st.dataframe(df)
