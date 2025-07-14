# --- llm_response.py ---
import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from prompt import classifier_prompt, generate_llm_report, chat_prompt
from chat_manager import ChatHistoryManager
from logger_util import setup_logger
from groq import Groq

load_dotenv()
logger = setup_logger(__name__)

class LLMResponse:
    def __init__(self):
        self.url = None
        self.data_fetcher = None
        self.review_fetcher = None
        self.driver = None
        self.question = None
        self.chat_history = ChatHistoryManager()
        file_path = r"D:\product_enhancer\human_data.json"
        with open(file_path, "r") as file:
            self.customer_profile = json.load(file)

        # Data placeholders
        self.info: Optional[Dict[str, Any]] = None
        self.tech_spec: Optional[Dict[str, Any]] = None
        self.generate_info: Optional[Dict[str, Any]] = None
        self.total_info: Optional[Dict[str, Any]] = None
        self.report_result: Optional[Dict[str, Any]] = None
        self.search_similar_items: List[Dict[str, Any]] = []
        self.search_youtube: List[Dict[str, Any]] = []
        self.relevant_search_items: List[List[Dict[str, Any]]] = []
        self.reviews: List[Dict[str, Any]] = []

        # Load Groq API client
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise EnvironmentError("GROQ_API_KEY not found in environment variables")

        self.client = Groq(api_key=groq_api_key)
        self.model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        logger.info(f"Groq model loaded: {self.model_name}")
    
    def _query_llm(self, prompt: str, system_prompt: str = "You are a helpful product classification assistant.") -> Dict[str, Any]:
        logger.info(f"[LLM] Querying Groq for URL: {self.url}")
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=1024
            )
            response_text = chat_completion.choices[0].message.content.strip()
            logger.debug(f"[LLM] Raw Response:\n{response_text}")

            # Try parsing JSON response
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.exception("Failed to decode JSON from LLM response")
            return {"error": "Invalid JSON response from LLM"}
        except Exception as e:
            logger.exception("Unexpected error querying LLM")
            return {"error": str(e)}

    def _query_llm_report(self, prompt: str, system_prompt: str = "You are a helpful product classification assistant.") -> str:
        logger.info(f"[LLM] Querying Groq for URL: {self.url}")
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=4096
            )
            response_text = chat_completion.choices[0].message.content.strip()
            logger.debug(f"[LLM] Markdown Response:\n{response_text}")
            return response_text
        except Exception as e:
            logger.exception("Error querying LLM for markdown response")
            return f"**Error:** {str(e)}"
    
    def chat_conversation(self, prompt: str) -> str:
        logger.info(f"[LLM] Chat conversation for URL: {self.url}")
        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096  
            )
            response_text = chat_completion.choices[0].message.content.strip()
            logger.debug(f"[LLM] Chat Response:\n{response_text}")          
            # Append to chat history
            self.chat_history.append(url=self.url, question=self.question, conversation_response=response_text)
            return response_text  
        except Exception as e:
            logger.exception("Error during chat conversation")
            return f"**Error:** {str(e)}"

    def run(self, url: str, data_fetcher, review_fetcher, driver=None) -> Dict[str, Any]:
        self.url = url
        self.data_fetcher = data_fetcher
        self.review_fetcher = review_fetcher
        self.driver = driver
        logger.info(f"Running LLM pipeline for: {self.url}")

        # Step 1: Fetch product information
        self.info = self.data_fetcher.fetch_product_info(url, driver)
        self.tech_spec = self.info.get('technical_specifications', {})
        if not self.info or self.info.get("title") == "Title not found" or self.info.get("error"):
            logger.warning("Product information is incomplete or missing.")
            return {"error": "Product data not available"}

        # Step 2: Fetch similar items and YouTube videos
        self.search_similar_items = self.data_fetcher.fetch_similar_items(self.info.get("title", ""))
        self.search_youtube = self.data_fetcher.fetch_youtube_videos(self.info.get("title", ""))

        # Step 3: Classify product using LLM
        classifier_input = classifier_prompt(self.info)
        self.generate_info = self._query_llm(classifier_input)

        # Step 4: Fetch reviews if available
        self.reviews = self.review_fetcher.get_reviews_from_url(url) if self.review_fetcher else []

        # Step 5: Fetch relevant search items based on LLM suggestions
        relevant_items = self.generate_info.get("relevant_items", [])
        if not isinstance(relevant_items, list):
            logger.warning("'relevant_items' is not a valid list.")
            relevant_items = []

        self.relevant_search_items = [
            self.data_fetcher.fetch_similar_items(item) for item in relevant_items
        ]
        # step 6: Getting customer profile
        customer_data = {
            "user_id": self.customer_profile.get("user_id", "unknown_user"),
            "name": self.customer_profile.get("name", "Unknown"),
            "location": self.customer_profile.get("location", "Unknown"),
            "review_tone": self.customer_profile.get("review_tone", 0),
            "decision_style": self.customer_profile.get("decision_style", 0),
        }
        if self.generate_info.get("product_classifier") == "Electronics":
            customer_data["preferences"] = self.customer_profile.get("categories", {}).get("Electronics", {})
        elif self.generate_info.get("product_classifier") == "Clothes":
            customer_data["preferences"] = self.customer_profile.get("categories", {}).get("Clothes", {})
        elif self.generate_info.get("product_classifier") == "Food":
            customer_data["preferences"] = self.customer_profile.get("categories", {}).get("Food", {})
        else:
            customer_data["preferences"] = {}
        # Step 7: Build combined dataset and generate final report
        self.total_info = {
            "classification_result": self.generate_info,
            "product_info": self.info,
            "specifications": self.tech_spec,
            "reviews": self.reviews,
            "similar_items": self.search_similar_items,
            "youtube_videos": self.search_youtube,
            "relevant_search_items": self.relevant_search_items,
            "customer_data": customer_data
        }
        logger.info(f"[LLM] Total info prepared for report")
        report_prompt = generate_llm_report(self.total_info)
        logger.info(f"[LLM] Report prompt: {report_prompt}")
        logger.info(f"[LLM] Generating final product report.")

        self.report_result = self._query_llm_report(
            report_prompt,
            system_prompt="You are a helpful assistant that generates well-formatted product summaries and recommendations."
        )

        return self.report_result or {"error": "Failed to generate final report."}

    def run_chat_conversation(self) -> str:
        logger.info(f"Running chat conversation for URL: {self.url}")
        chat_history_conversation = self.chat_history.get_last_n(self.url, 3)
        logger.info(f"Chat history before conversation: {self.chat_history}")
        prompt = chat_prompt(self.total_info, chat_history_conversation, self.question)
        logger.info(f"Chat prompt: {prompt}")
        response = self.chat_conversation(prompt)
        logger.debug(f"Chat response: {response}")
        return response
