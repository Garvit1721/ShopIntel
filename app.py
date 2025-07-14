# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from logger_util import setup_logger
from logger_context import call_id_var
from data_fetcher import DataFetcher
from llm_response import LLMResponse
from driver_manager import DriverManager
from review_fetcher import ReviewFetcher
import uuid
from dotenv import load_dotenv
import os
import atexit

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
logger = setup_logger("app")

# Initialize components
driver_manager = DriverManager()
llm_handler = LLMResponse()
review_fetcher = ReviewFetcher()
data_fetcher = DataFetcher()

# Safe shutdown
@atexit.register
def graceful_shutdown():
    try:
        if driver_manager and driver_manager.started:
            logger.info("[Shutdown] Gracefully shutting down Chrome driver...")
            driver_manager.shutdown_driver()
    except Exception as e:
        logger.warning(f"[Shutdown] Exception during driver shutdown: {e}")

@app.before_request
def log_request():
    print(f"[Flask] {request.method} {request.url}")
    print(f"[Headers] {dict(request.headers)}")
    print(f"[Body] {request.get_data(as_text=True)}")

@app.route("/analyze-url", methods=["POST"])
def analyze_url():
    try:
        call_id_var.set(str(uuid.uuid4()))
        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "URL is required"}), 400

        logger.info(f"Received analyze request for: {url}")
        driver = driver_manager.get_driver()
        markdown_result = llm_handler.run(url, data_fetcher, review_fetcher, driver)
        return jsonify({"markdown": markdown_result})

    except Exception as e:
        logger.exception("Error during /analyze-url")
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        call_id_var.set(str(uuid.uuid4()))
        data = request.get_json()
        url = data.get("url")
        question = data.get("question")

        if not url or not question:
            return jsonify({"error": "Missing URL or question"}), 400

        logger.info(f"Chat request for: {url}")
        llm_handler.url = url
        llm_handler.question = question

        if not llm_handler.total_info:
            driver = driver_manager.get_driver()
            llm_handler.run(url, data_fetcher, review_fetcher, driver)

        response = llm_handler.run_chat_conversation()
        return jsonify({"answer": response})

    except Exception as e:
        logger.exception("Error during /chat")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=4000, debug=True)
