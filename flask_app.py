from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data['prompt']
    
    # Generate a response using the existing generate_response function
    bot_response = generate_response(user_message)

    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True)
