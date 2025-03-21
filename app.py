from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
import json
import time
import requests
from bs4 import BeautifulSoup
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
csrf = CSRFProtect(app)

# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load scraper configuration from config.json
CONFIG_PATH = "config.json"
def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

# Scraping function using the configuration file
def nova_scraper():
    config = load_config()
    headers = {"User-Agent": config.get("user_agent", "NOVA-Scraper/1.0")}
    results = []

    # Loop through each URL specified in config.json
    for url in config.get("urls", []):
        while url:
            try:
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")

                # Get list of items using the CSS selector from config
                items = soup.select(config["parser"]["items"])
                for item in items:
                    # Safely extract each field using selectors
                    title_elem = item.select_one(config["parser"]["fields"]["title"]["selector"])
                    price_elem = item.select_one(config["parser"]["fields"]["price"]["selector"])
                    url_elem = item.select_one(config["parser"]["fields"]["url"]["selector"])
                    image_elem = item.select_one(config["parser"]["fields"]["image"]["selector"])

                    scraped_data = {
                        "title": title_elem.get_text(strip=True) if title_elem else "",
                        "price": price_elem.get_text(strip=True) if price_elem else "",
                        "url": url_elem["href"] if url_elem and url_elem.has_attr("href") else "",
                        "image": image_elem["src"] if image_elem and image_elem.has_attr("src") else ""
                    }
                    results.append(scraped_data)

                # Handle pagination if next page exists
                next_page_elem = soup.select_one(config["parser"]["pagination"]["next_selector"])
                if next_page_elem and next_page_elem.has_attr(config["parser"]["pagination"]["attribute"]):
                    next_href = next_page_elem[config["parser"]["pagination"]["attribute"]]
                    # Construct next URL using base_url if necessary
                    url = config["parser"]["pagination"].get("base_url", "") + next_href
                else:
                    url = None

                time.sleep(config.get("delay", 2))
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                break
    return results

# Dummy search function for API (replace with your own search logic)
def perform_search(query, filters):
    # This dummy implementation returns some fake results based on the query.
    dummy_results = {
        "count": 25,
        "results": [
            {
                "id": i,
                "source": "Example",
                "username": f"user{i}",
                "content": f"Result content for '{query}' number {i}",
                "date": "2023-01-01",
                "relevance": 0.7 + (i % 3) * 0.1  # Dummy relevance score
            }
            for i in range(1, 26)
        ]
    }
    # In a real app, apply filters, sorting, etc.
    return dummy_results

# --------------------
# Routes
# --------------------

@app.route('/')
def index():
    return render_template('index.html', user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    # Optionally, you can perform scraping on-demand or show recent scrapes.
    scrape_results = nova_scraper()
    return render_template('dashboard.html', user=current_user, scrape_results=scrape_results)

@app.route('/search_history')
@login_required
def search_history():
    # For demonstration, using dummy history data.
    history_data = [
        {'timestamp': '2023-03-15 10:00', 'url': 'https://example.com', 'items_scraped': 5},
        {'timestamp': '2023-03-16 14:20', 'url': 'https://another.com', 'items_scraped': 10}
    ]
    return render_template('search_history.html', recent_history=history_data)

@app.route('/analytics')
@login_required
def analytics():
    return "Nothing here."


@app.route('/settings')
@login_required
def settings():
    return "Nothing here."


@app.route('/help_page')
@login_required
def help_page():
    return "Nothing here."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        print(f"{username} {email} {password}")
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')
        if User.query.filter((User.username==username) | (User.email==email)).first():
            flash("Username or Email already exists.", "danger")
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for('index'))

# API endpoint for search (used by main.js)
@app.route('/search', methods=['POST'])
@csrf.exempt  # If you handle CSRF manually in your JS, you can exempt this route or include the token
def search():
    data = request.get_json()
    query = data.get('query', '').strip()
    filters = data.get('filters', {})
    if not query:
        return jsonify({"error": "Empty search query"}), 400
    search_results = perform_search(query, filters)
    return jsonify(search_results)

# --------------------
# Main entry point
# --------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database tables if they don't exist
    app.run(debug=True)
