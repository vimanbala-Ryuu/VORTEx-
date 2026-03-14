# FinPay by VORTEx 🚀

FinPay is a full-stack, responsive fintech web application simulator. It demonstrates modern neobanking features including automated round-up savings, live QR code scanning, multi-user authentication, and gamified reward milestones.

Designed with a lightweight yet robust architecture, it features persistent SQLite database storage and a custom-built, pure-Python Machine Learning engine to predict user spending habits without relying on heavy external data science libraries.

## ✨ Key Features

* **Secure User Authentication:** Full multi-user support with account registration, secure login, and session-based state management. Every user gets their own isolated balance, transaction history, and milestone tracking.
* **Persistent Data Storage:** Fully integrated with SQLite and SQLAlchemy, ensuring all user data, transactions, and progress survive server restarts.
* **Round-Up Auto-Savings:** Simulates spare change investing by automatically rounding up transactions to the nearest ₹10 or ₹100 and routing the difference to a "Virtual Piggy Bank."
* **Pure Python ML Spend Prediction:** Uses a from-scratch implementation of Ordinary Least Squares (Linear Regression) to forecast future transaction amounts based on historical data arrays.
* **Dynamic User Profiles & QR:** Generates personalized, live UPI QR codes for every registered user to simulate peer-to-peer receiving.
* **Gamified Milestones:** Tracks category-specific spending targets. Upon completion, a weighted randomizer dispenses pure cash rewards or discount coupons (e.g., Domino's, Amazon, Uber).
* **Live QR Code Scanner:** Integrates your device's camera to scan real-world UPI QR codes, decode the payload, and auto-fill the payment pipeline.
* **Polished Fintech UI:** A responsive, mobile-first design that automatically expands into a comprehensive dual-column dashboard on desktop, featuring a modern, dark-mode glassmorphic aesthetic with subtle neon accents. Includes an expandable "View More" recent activity feed.

## 🛠️ Tech Stack

**Backend & Data Layer:**

* **Python 3:** Core logic, routing, and mathematical modeling.
* **Flask:** Lightweight WSGI web application framework.
* **Flask-SQLAlchemy & SQLite:** ORM and relational database management for persistent data storage.
* **Standard Libraries:** `math`, `random`, `datetime`, `os`.

**Frontend UI/UX:**

* **HTML5 / CSS3:** Custom, framework-free responsive styling utilizing CSS Grid, Flexbox, and backdrop-filter glassmorphism.
* **Vanilla JavaScript:** DOM manipulation, asynchronous API fetches (`fetch`), session handling, and state rendering.
* **Libraries & APIs:** `html5-qrcode` (camera scanning), UI Avatars API, QR Server API.

## 📁 Project Structure

```text
FinPay_Simulator/
│
├── app.py                  # Main Flask server, auth logic, ML engine, and API routes
├── finpay.db               # SQLite relational database (auto-generated on run)
├── static/                 
│   └── logo.jpeg           # Application branding
└── templates/              
    └── index.html          # Frontend UI, CSS styling, and JS controllers

```

## 🚀 Quick Start

1. **Install Dependencies:** Ensure you have Python installed, then install the required packages:
```bash
pip install Flask Flask-SQLAlchemy

```


2. **Run the Server:**
```bash
python app.py

```


3. **Access the App:**
Open your browser and navigate to `http://localhost:5000`. Create a new account to initialize your personal database profile and start exploring!
