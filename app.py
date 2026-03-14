from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import math
import random

app = Flask(__name__)
app.secret_key = 'finpay_vortex_super_secret'

# --- Database Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finpay.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False) # In production, hash this!
    main_balance = db.Column(db.Float, default=0.0)
    piggy_bank = db.Column(db.Float, default=0.0)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    milestones = db.relationship('Milestone', backref='user', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(20))
    type = db.Column(db.String(20))
    amount = db.Column(db.Float)
    category = db.Column(db.String(50))
    receiver = db.Column(db.String(100))
    upi = db.Column(db.String(100))

    def to_dict(self):
        return {"id": self.id, "date": self.date, "type": self.type, "amount": self.amount, "category": self.category, "receiver": self.receiver, "upi": self.upi}

class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    desc = db.Column(db.String(100))
    target = db.Column(db.Float)
    progress = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(50))
    done = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {"id": self.id, "desc": self.desc, "target": self.target, "progress": self.progress, "category": self.category, "done": self.done}

# --- Initialize Database ---
with app.app_context():
    db.create_all()

# --- Helpers ---
def get_current_user():
    username = session.get('username')
    if not username: return None
    return User.query.filter_by(username=username).first()

def add_default_milestones(user):
    defaults = [
        {"desc": "Spend ₹500 total", "target": 500, "category": "Any"},
        {"desc": "Spend ₹300 on Food", "target": 300, "category": "Food"},
        {"desc": "Spend ₹1000 on Travel", "target": 1000, "category": "Travel"},
        {"desc": "Spend ₹500 on Shopping", "target": 500, "category": "Shopping"},
        {"desc": "Spend ₹200 on Recharge", "target": 200, "category": "Recharge"},
    ]
    for m in defaults:
        new_m = Milestone(user_id=user.id, desc=m['desc'], target=m['target'], category=m['category'])
        db.session.add(new_m)
    db.session.commit()

def predict_next_spend(spends):
    n = len(spends)
    if n < 2: return spends[0] if n == 1 else 0.0
    x = list(range(1, n + 1)) 
    y = spends                
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    if denominator == 0: return mean_y
    m = numerator / denominator
    b = mean_y - m * mean_x
    return max(0.0, (m * (n + 1)) + b) 

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password: return jsonify({"error": "Required"}), 400
    if User.query.filter_by(username=username).first(): return jsonify({"error": "User exists"}), 400
        
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit() # Commit to get the user ID
    
    add_default_milestones(new_user)
    session['username'] = username
    return jsonify({"success": True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.password == data.get('password'):
        session['username'] = user.username
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"success": True})

@app.route('/api/state', methods=['GET'])
def get_state():
    user = get_current_user()
    if not user: return jsonify({"error": "Unauthorized"}), 401

    txs = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.id.desc()).all()
    analytics = {}
    spends = []
    
    for t in txs:
        if t.type == 'Spend':
            analytics[t.category] = analytics.get(t.category, 0) + t.amount
            spends.insert(0, t.amount) # Insert at 0 to keep chronological order for ML

    ai_offer = "Keep spending to unlock personalized AI offers!"
    if analytics:
        top_category = max(analytics, key=analytics.get)
        ai_offer = f"✨ AI Insight: You love {top_category}! Spend more here for rewards!"

    prediction = "Need more data to predict."
    if len(spends) > 1:
        prediction = f"🔮 ML Predicts next spend: ₹{round(predict_next_spend(spends), 2)}"

    active_m = Milestone.query.filter_by(user_id=user.id, done=False).first()

    return jsonify({
        "username": user.username,
        "account": {"main_balance": user.main_balance, "piggy_bank": user.piggy_bank},
        "transactions": [t.to_dict() for t in txs],
        "active_milestone": active_m.to_dict() if active_m else None,
        "prediction": prediction,
        "ai_offer": ai_offer
    })

@app.route('/api/add_money', methods=['POST'])
def add_money():
    user = get_current_user()
    if not user: return jsonify({"error": "Unauthorized"}), 401
    
    amount = float(request.json.get('amount', 0))
    if amount <= 0: return jsonify({"error": "Invalid amount"}), 400
    
    user.main_balance += amount
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_tx = Transaction(user_id=user.id, date=now, type="Deposit", amount=amount, category=request.json.get('method', 'Bank Transfer'), receiver="Main Account")
    
    db.session.add(new_tx)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/spend', methods=['POST'])
def spend_money():
    user = get_current_user()
    if not user: return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    amount = float(data.get('amount', 0))
    category = data.get('category', 'Others')
    round_to = int(data.get('round_to', 10))

    if amount <= 0: return jsonify({"error": "Invalid amount"}), 400

    platform_fee = 1.0 if amount > 50 else 0.0
    rounded_amount = math.ceil(amount / float(round_to)) * round_to
    spare_change = rounded_amount - amount
    total_deduction = amount + platform_fee + spare_change

    if user.main_balance < total_deduction:
        return jsonify({"error": "Insufficient funds"}), 400

    # Deduct balances
    user.main_balance -= total_deduction
    user.piggy_bank += spare_change

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.session.add(Transaction(user_id=user.id, date=now, type="Spend", amount=amount, category=category, receiver=data.get('receiver_name', 'Merchant'), upi=data.get('upi_id', 'Unknown')))
    
    if platform_fee > 0:
        db.session.add(Transaction(user_id=user.id, date=now, type="Fee", amount=platform_fee, category="Platform Fee", receiver="FinPay Network"))
    if spare_change > 0:
        db.session.add(Transaction(user_id=user.id, date=now, type="Round-Up", amount=round(spare_change, 2), category=f"Saved (Nearest ₹{round_to})", receiver="Piggy Bank"))

    # Milestone Logic
    active_m = Milestone.query.filter_by(user_id=user.id, done=False).first()
    if active_m and (active_m.category == 'Any' or active_m.category == category):
        active_m.progress += amount
        if active_m.progress >= active_m.target:
            active_m.done = True
            
            reward_type = random.choice(['cash', 'cash', 'food_coupon', 'travel_coupon'])
            if reward_type == 'cash':
                cash_reward = random.randint(1, 5) if random.random() < 0.75 else random.randint(6, 9)
                user.piggy_bank += cash_reward
                db.session.add(Transaction(user_id=user.id, date=now, type="Cashback", amount=cash_reward, category="Reward", receiver=f"₹{cash_reward} Cash!"))
            else:
                db.session.add(Transaction(user_id=user.id, date=now, type="Coupon", amount=0, category="Reward", receiver="Discount Coupon!"))

    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/donate', methods=['POST'])
def donate():
    user = get_current_user()
    if not user: return jsonify({"error": "Unauthorized"}), 401

    amount = float(request.json.get('amount', 0))
    if amount <= 0 or user.main_balance < amount:
        return jsonify({"error": "Invalid amount or Insufficient funds"}), 400

    user.main_balance -= amount
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.session.add(Transaction(user_id=user.id, date=now, type="Donation", amount=amount, category="Charity", receiver=request.json.get('charity', 'General Fund')))
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/redeem', methods=['POST'])
def redeem():
    user = get_current_user()
    if not user: return jsonify({"error": "Unauthorized"}), 401

    if user.piggy_bank > 0:
        amount = user.piggy_bank
        user.main_balance += amount
        user.piggy_bank = 0.0
        db.session.add(Transaction(user_id=user.id, date=datetime.now().strftime("%Y-%m-%d %H:%M"), type="Redeem", amount=round(amount, 2), category="Piggy Bank to Main", receiver="Self"))
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Empty"}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')