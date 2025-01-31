from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote_plus
from datetime import datetime
import os

app = Flask(__name__)

# Proper MongoDB URI encoding
MONGO_USERNAME = quote_plus(os.getenv("MONGO_USERNAME", "admin"))
MONGO_PASSWORD = quote_plus(os.getenv("MONGO_PASSWORD", "admin@123"))
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER", "cluster0.pkdkx.mongodb.net")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "inventory.materials")

MONGO_URI = f"mongodb+srv://<admin>:<admin@123>@cluster0.pkdkx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)

# Route: Homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route: Dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ✅ Register API
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        hashed_password = generate_password_hash(data['password'], method='sha256')

        if mongo.db.users.find_one({"username": data['username']}):
            return jsonify({"error": "User already exists"}), 400

        mongo.db.users.insert_one({
            "username": data['username'],
            "password": hashed_password,
            "role": data.get('role', 'user')
        })
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Login API
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = mongo.db.users.find_one({"username": data['username']})
        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({"error": "Invalid credentials"}), 401

        return jsonify({"message": "Login successful"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Create & Fetch Projects
@app.route('/api/projects', methods=['GET', 'POST'])
def projects():
    try:
        if request.method == 'GET':
            projects = list(mongo.db.projects.find({}, {"_id": 0}))
            return jsonify(projects)

        elif request.method == 'POST':
            data = request.json
            mongo.db.projects.insert_one({
                "name": data['name'],
                "inventory": [],
                "required_materials": [],
                "logs": []
            })
            return jsonify({"message": "Project created"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Update Inventory
@app.route('/api/projects/<project_name>/inventory', methods=['PUT'])
def update_inventory(project_name):
    try:
        data = request.json
        action = data.get('action')  # 'add' or 'remove'
        quantity = data.get('quantity', 0)
        item_name = data['name']

        project = mongo.db.projects.find_one({"name": project_name})
        if not project:
            return jsonify({"error": "Project not found"}), 404

        inventory = project.get('inventory', [])

        # Find item in inventory
        item_found = False
        for item in inventory:
            if item['name'] == item_name:
                if action == 'remove' and item['quantity'] < quantity:
                    return jsonify({"error": "Not enough stock"}), 400
                item['quantity'] += quantity if action == 'add' else -quantity
                item_found = True
                break

        # If item is not found and action is 'add', add it
        if not item_found and action == 'add':
            inventory.append({"name": item_name, "quantity": quantity})

        mongo.db.projects.update_one({"name": project_name}, {"$set": {"inventory": inventory}})
        return jsonify({"message": "Inventory updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
