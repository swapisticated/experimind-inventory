from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote_plus
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# Add this line to debug
print("MONGO_URI:", os.getenv('MONGO_URI'))

app = Flask(__name__)

# MongoDB Atlas Configuration
MONGO_URI = os.getenv('MONGO_URI', 'your_default_uri')  # Get from environment variable

# Configure MongoDB with SSL settings
app.config["MONGO_URI"] = MONGO_URI
app.config["MONGO_SSL"] = True
app.config["MONGO_SSL_CERT_REQS"] = None  # Don't verify SSL certificate
app.config["MONGO_CONNECT_TIMEOUT_MS"] = 30000  # Increase timeout
app.config["MONGO_SOCKET_TIMEOUT_MS"] = 30000  # Increase timeout

mongo = PyMongo(app)

logging.basicConfig(level=logging.DEBUG)

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
        logging.debug(f"Registration attempt with data: {data}")
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"error": "Missing username or password"}), 400

        # Using the full method name for password hashing
        hashed_password = generate_password_hash(
            data['password'], 
            method='pbkdf2:sha256', 
            salt_length=8
        )

        if mongo.db.users.find_one({"username": data['username']}):
            return jsonify({"error": "User already exists"}), 400

        result = mongo.db.users.insert_one({
            "username": data['username'],
            "password": hashed_password,
            "role": data.get('role', 'user')
        })
        logging.debug(f"User created with id: {result.inserted_id}")
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Login API
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        logging.debug(f"Login attempt for username: {data.get('username', 'no username provided')}")
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"error": "Missing username or password"}), 400

        user = mongo.db.users.find_one({"username": data['username']})
        if not user:
            logging.debug("User not found in database")
            return jsonify({"error": "Invalid credentials"}), 401

        if not check_password_hash(user['password'], data['password']):
            logging.debug("Password check failed")
            return jsonify({"error": "Invalid credentials"}), 401

        logging.debug("Login successful")
        return jsonify({"message": "Login successful"}), 200

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
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

# ✅ Test Database Connection
@app.route('/api/test-db')
def test_db():
    try:
        # Test the connection
        mongo.db.command('ping')
        
        # Get database info
        db_stats = mongo.db.command('dbstats')
        
        # Get collection names
        collections = mongo.db.list_collection_names()
        
        return jsonify({
            "message": "Connected to MongoDB!",
            "database_name": mongo.db.name,
            "collections": list(collections),
            "stats": db_stats
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Database connection failed: {str(e)}",
            "uri": MONGO_URI.replace(quote_plus(os.getenv("MONGO_PASSWORD", "admin@123")), "****")  # Hide password in output
        }), 500

# Add this near your other routes
@app.route('/api/routes')
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "path": str(rule)
        })
    return jsonify(routes)

# Get all resources
@app.route('/api/resources', methods=['GET', 'POST'])
def resources():
    try:
        if request.method == 'GET':
            resources = list(mongo.db.resources.find({}, {"_id": 0}))
            return jsonify(resources)
        
        elif request.method == 'POST':
            data = request.json
            if mongo.db.resources.find_one({"name": data['name']}):
                return jsonify({"error": "Resource already exists"}), 400
                
            # Set available_quantity equal to max_units initially
            max_units = data['max_units']
            mongo.db.resources.insert_one({
                "name": data['name'],
                "max_units": max_units,
                "available_quantity": max_units  # Set to max initially
            })
            return jsonify({"message": "Resource added"}), 201

    except Exception as e:
        logging.error(f"Error in resources: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Update required quantity
@app.route('/api/resources/<resource_name>/required', methods=['PUT'])
def update_required(resource_name):
    try:
        data = request.json
        quantity = int(data['quantity'])
        
        mongo.db.resources.update_one(
            {"name": resource_name},
            {"$set": {"required_quantity": quantity}}
        )
        return jsonify({"message": "Required quantity updated"}), 200

    except Exception as e:
        logging.error(f"Error in update_required: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Update available quantity
@app.route('/api/resources/<resource_name>/quantity', methods=['PUT'])
def update_quantity(resource_name):
    try:
        data = request.json
        change = int(data['change'])
        
        resource = mongo.db.resources.find_one({"name": resource_name})
        if not resource:
            return jsonify({"error": "Resource not found"}), 404
            
        new_quantity = resource.get('available_quantity', 0) + change
        if new_quantity < 0:
            return jsonify({"error": "Not enough quantity available"}), 400
            
        if new_quantity > resource['max_units']:
            return jsonify({"error": "Cannot exceed maximum units"}), 400
            
        mongo.db.resources.update_one(
            {"name": resource_name},
            {"$set": {"available_quantity": new_quantity}}
        )
        return jsonify({"message": "Quantity updated"}), 200

    except Exception as e:
        logging.error(f"Error in update_quantity: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
