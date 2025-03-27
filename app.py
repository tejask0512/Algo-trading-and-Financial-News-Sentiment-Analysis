from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for, session, flash
import subprocess
import pandas as pd
import threading
import time
import os
import sqlite3
import re
import hashlib
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__, template_folder="templates", static_folder="static")

# Secret key for session management
app.secret_key = "Greez@1336"

# Absolute paths to scripts and data
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SCRAPER_PATH = os.path.join(BASE_DIR, "scraper.py")
print(f"THis is the {SCRAPER_PATH}")
SENTIMENT_PATH = os.path.join(BASE_DIR, "sentiment_analysis_pipeline.py")
print(f"This is sentiment path {SENTIMENT_PATH}")
SENTIMENT_RESULTS = os.path.join(DATA_DIR, "sentiment_results.csv")
USER_DB = os.path.join(DATA_DIR, "user.db")

# User authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Password utility functions
def is_valid_password(password):
    """Check if password meets complexity requirements"""
    # At least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special character
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def is_valid_email(email):
    """Check if email has valid format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_phone(phone):
    if len(phone)==10:
        return True
    return False

# Initialize database
def init_db():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            phone INTEGER UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Background task to run scraper and sentiment analysis
def run_scraper_and_sentiment_analysis():
    """Runs scraper and sentiment analysis every 30 minutes."""
    while True:
        try:
            print("Running scraper...")
            subprocess.run(["python", SCRAPER_PATH], check=True)

            print("Running sentiment analysis pipeline...")
            subprocess.run(["python", SENTIMENT_PATH], check=True)

            print("Data updated successfully.")
        except Exception as e:
            print(f"Error updating data: {e}")

        # Wait before running again (every 30 minutes)
        time.sleep(1800)

# Start background thread for data processing
threading.Thread(target=run_scraper_and_sentiment_analysis, daemon=True).start()

# Routes

@app.route('/')
def home():
    # Check if user is already logged in
    if "user_id" in session:  
        return redirect(url_for('mainpage'))  # User is logged in, go to dashboard
    
    # Check if this is a new visitor or a returning visitor
    if session.get('visited_before'):
        # Not a first-time visitor, go to login
        return redirect(url_for('login'))
    else:
        # Mark the user as having visited before
        session['visited_before'] = True
        # First-time visitor, go to registration
        return redirect(url_for('register'))

@app.route("/dashboard")
@login_required
def dashboard():
    
    return render_template("dashboard.html", user_name=session.get("user_name")) 

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash, name FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["user_name"] = user[2]
            session["user_email"] = email
            
            # Update last login time
            conn = sqlite3.connect(USER_DB)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user[0],))
            conn.commit()
            conn.close()
            
            # Redirect to dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for("mainpage"))
        else:
            flash("Invalid email or password", "error")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # Check if user is already logged in
    if "user_id" in session:
        return redirect(url_for('mainpage'))  # User is logged in, go to dashboard
        
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        username = request.form.get("username")
        phone=request.form.get("phone")
        
        # Validate input
        if not all([email, phone, password, confirm_password, username]):
            flash("All fields are required", "error")
            return render_template("register.html")
        if not is_valid_phone(phone):
            flash("PLease Enter Valid Phone Number")
            return render_template("register.html")
        
        if not is_valid_email(email):
            flash("Invalid email format", "error")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")
        
        if not is_valid_password(password):
            flash("Password should be at least 8 characters with at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character", "error")
            return render_template("register.html")
        
        # Check if email already exists
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            flash("Email already registered", "error")
            return render_template("register.html")
        
        # Create new user
        password_hash = generate_password_hash(password)

        cursor.execute("INSERT INTO users (email, phone, password_hash, name) VALUES (?, ?, ?, ?)", 
                      (email, phone, password_hash, username))
        conn.commit()
        conn.close()
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

@app.route("/mainpage")
@login_required
def mainpage():
    return render_template("mainpage.html", user_name=session.get("user_name"), current_user=session)

@app.route("/profile")
@login_required
def profile():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT email, name, created_at, last_login FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        flash("User not found", "error")
        return redirect(url_for("login"))
    
    user_data = {
        "email": user[0],
        "name": user[1],
        "created_at": user[2],
        "last_login": user[3]
    }
    
    return render_template("profile.html", user_data=user_data)

@app.route("/reset_password", methods=["GET", "POST"])
@login_required
def reset_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        # Validate input
        if not all([current_password, new_password, confirm_password]):
            flash("All fields are required", "error")
            return render_template("reset_password.html")
        
        if new_password != confirm_password:
            flash("New passwords do not match", "error")
            return render_template("reset_password.html")
        
        if not is_valid_password(new_password):
            flash("Password should be at least 8 characters with at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character", "error")
            return render_template("reset_password.html")
        
        # Verify current password
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],))
        stored_password_hash = cursor.fetchone()[0]
        
        if not check_password_hash(stored_password_hash, current_password):
            conn.close()
            flash("Current password is incorrect", "error")
            return render_template("reset_password.html")
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", 
                      (new_password_hash, session["user_id"]))
        conn.commit()
        conn.close()
        
        flash("Password updated successfully", "success")
        return redirect(url_for("profile"))
    
    return render_template("reset_password.html")

@app.route("/settings")
@login_required
def settings():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT email, name FROM users WHERE id = ?", (session["user_id"],))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        flash("User not found", "error")
        return redirect(url_for("login"))
    
    user = {
        "email": user_data[0],
        "name": user_data[1]
    }
    
    return render_template("settings.html", user=user)

@app.route("/update_settings", methods=["POST"])
@login_required
def update_settings():
    new_name = request.form.get("name")
    email = request.form.get("email")
    
    if not new_name or not email:
        flash("Name and email are required", "error")
        return redirect(url_for("settings"))
    
    if not is_valid_email(email):
        flash("Invalid email format", "error")
        return redirect(url_for("settings"))
    
    # Check if email already exists (for other users)
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, session["user_id"]))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        flash("Email already in use by another account", "error")
        return redirect(url_for("settings"))
    
    # Update user info
    cursor.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", 
                  (new_name, email, session["user_id"]))
    conn.commit()
    conn.close()
    
    # Update session
    session["user_name"] = new_name
    session["user_email"] = email
    
    flash("Settings updated successfully", "success")
    return redirect(url_for("settings"))

# Trading livechart route
@app.route("/TradingLivechart-Development.html")
@login_required
def trading_livechart():
    """Renders the trading livechart."""
    return render_template("TradingLivechart-Development.html")

@app.route("/faq")
@login_required
def faq():
    """Renders the trading livechart."""
    return render_template("faq.html")

@app.route("/policy")
@login_required
def policy():
    """Renders the trading livechart."""
    return render_template("privacypolicy.html")

# Stock news impact dashboard route
@app.route("/StockNewsImpact.html")
@login_required
def stock_news_impact():
    """Renders the stock news impact dashboard."""
    return render_template("StockNewsImpact.html")

# API endpoint for news data
@app.route("/api/news")
@login_required
def get_news():
    """Returns the latest news from sentiment_results.csv."""
    if not os.path.exists(SENTIMENT_RESULTS):
        return jsonify({"error": "Sentiment results file not found"}), 500

    df = pd.read_csv(SENTIMENT_RESULTS).fillna("")
    news_data = df.to_dict(orient="records")

    return jsonify({"news": news_data})

# Serve static files
@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
