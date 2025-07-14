# --- chat_manager.py ---
import os
import pandas as pd
from datetime import datetime
from logger_util import setup_logger

logger = setup_logger(__name__)

class ChatHistoryManager:
    def __init__(self):
        self.history_dir = "chat_logs"
        self.filename = "history.csv"
        self.filepath = os.path.join(self.history_dir, self.filename)
        os.makedirs(self.history_dir, exist_ok=True)
        self.columns = ["timestamp", "url", "question", "conversation_response"]

    def _read_history(self) -> pd.DataFrame:
        if not os.path.exists(self.filepath):
            return pd.DataFrame(columns=self.columns)
        try:
            df = pd.read_csv(self.filepath)
            missing = set(self.columns) - set(df.columns)
            if missing:
                logger.warning(f"History file is missing columns: {missing}. Resetting.")
                return pd.DataFrame(columns=self.columns)
            return df
        except Exception as e:
            logger.warning(f"Failed to read chat history: {e}")
            return pd.DataFrame(columns=self.columns)

    def append(self, url: str, question: str, conversation_response: str, retain_last_n: int = 3):
        if not url:
            logger.warning("No URL provided. Skipping append.")
            return

        timestamp = datetime.utcnow().isoformat()
        new_row = pd.DataFrame([{
            "timestamp": timestamp,
            "url": url,
            "question": question or "",
            "conversation_response": conversation_response or ""
        }])

        history_df = self._read_history()
        history_df = pd.concat([history_df, new_row], ignore_index=True)
        filtered = history_df[history_df["url"] == url].sort_values("timestamp").tail(retain_last_n)
        other_urls = history_df[history_df["url"] != url]
        final_df = pd.concat([other_urls, filtered], ignore_index=True)

        try:
            final_df.to_csv(self.filepath, index=False)
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")

    def get_last_n(self, url: str, n: int = 3) -> str:
        if not url:
            return "No URL provided."

        history_df = self._read_history()
        url_df = history_df[history_df["url"] == url].sort_values("timestamp").tail(n)

        if url_df.empty:
            return "No previous history available for this product."

        result = []
        for i, row in enumerate(url_df.to_dict(orient="records"), 1):
            formatted = (
                f"--- Conversation {i} ({row['timestamp']}) ---\n"
                f"Question:\n{row.get('question', '').strip()}\n"
                f"Assistant Response:\n{row.get('conversation_response', '').strip()}\n"
            )
            result.append(formatted)

        return "\n".join(result)
