from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

# MongoDB configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://adarshgd:<Adarsh@0119>@cluster0.pkdkx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo = PyMongo(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    hashed_password = generate_password_hash(data['password'], method='sha256')
    mongo.db.users.insert_one({
        "username": data['username'],
        "password": hashed_password,
        "role": data.get('role', 'user')
    })
    return jsonify({"message": "User registered"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = mongo.db.users.find_one({"username": data['username']})
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"message": "Login successful"}), 200

@app.route('/api/projects', methods=['GET', 'POST'])
def projects():
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

@app.route('/api/projects/<project_name>/inventory', methods=['PUT'])
def update_inventory(project_name):
    data = request.json
    action = data.get('action')  # 'add' or 'remove'
    quantity = data.get('quantity', 0)
    item_name = data['name']

    project = mongo.db.projects.find_one({"name": project_name})
    if not project:
        return jsonify({"error": "Project not found"}), 404

    inventory = project['inventory']
    for item in inventory:
        if item['name'] == item_name:
            item['quantity'] += quantity if action == 'add' else -quantity
            break
    else:
        if action == 'add':
            inventory.append({"name": item_name, "quantity": quantity})

    mongo.db.projects.update_one({"name": project_name}, {"$set": {"inventory": inventory}})
    return jsonify({"message": "Inventory updated"}), 200

if __name__ == '__main__':
    app.run(debug=True)
