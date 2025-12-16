from flask import Flask, render_template, request, jsonify, session
import uuid
import os
from example_usage import EnhancedRAGChat

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "dev-secret-key")
chat_system = EnhancedRAGChat()

@app.route("/")
def index():
    """Serve the main chat interface"""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Process user messages"""
    data = request.get_json()
    user_message = data.get("message", "")
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    chat_system.session_id = session["session_id"]
    assistant_response = chat_system.chat(user_message)

    return jsonify({"response": assistant_response})

@app.route("/end", methods=["POST"])
def end_session():
    """Clear conversation memory"""
    if "session_id" in session:
        chat_system.end_session()
        session.clear()
    return jsonify({"message": "Session cleared"})


if __name__ == "__main__":
    app.run(debug=True)
