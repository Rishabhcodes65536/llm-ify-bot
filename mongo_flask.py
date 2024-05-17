from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import json_util

def jsonify_mongo(data):
    return json_util.dumps(data)

app = Flask(__name__)

# Update this to your MongoDB connection string
app.config["MONGO_URI"] = "mongodb://localhost:27017/chatbot_database"
mongo = PyMongo(app)

@app.route('/store', methods=['POST'])
def store_data():
    data = request.json
    user_message = data.get('user_message')
    ai_response = data.get('ai_response')
    
    if not user_message or not ai_response:
        return jsonify({"error": "Missing data"}), 400

    # Insert into MongoDB
    mongo.db.conversations.insert_one({
        "user_message": user_message,
        "ai_response": ai_response
    })

    return jsonify({"message": "Stored successfully"})

@app.route('/get-conversations', methods=['GET'])
def get_conversations():
    conversations = mongo.db.conversations.find()
    return jsonify(list(conversations))


if __name__ == '__main__':
    app.run(debug=True)
