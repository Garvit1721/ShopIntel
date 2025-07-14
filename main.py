# --- main.py ---
import uuid
from logger_util import setup_logger
from logger_context import call_id_var
from data_fetcher import DataFetcher
from llm_response import LLMResponse
from driver_manager import DriverManager
from review_fetcher import ReviewFetcher

logger = setup_logger(__name__)
call_id_var.set(str(uuid.uuid4()))

if __name__ == "__main__":
    url = "https://www.amazon.in/Vlogging-Camera-4K-Digital-YouTube/dp/B0BGLDXHGY/ref=sr_1_1_sspa?crid=1LBHC9MZJXELB&dib=eyJ2IjoiMSJ9.2tyTfTYlRJ1zSTJbsnz8cFK-hlCLTUWmrZmwwK_ACZl_uLZXwY5BUHhdH4-RQCpQfwMnIR6L0ZiunUiC6B1jVoQP61MN3nzoR0yHLHsJkrT593Pyl9bK8QGsqeT0o-FIZsMtd-TPsfnekz3oAuygXxCgcmPlqYKHQnxOevmZeZEiT82DFoBUnaa31I_zyPY7Rjz3btgrD6g6ZwT14TtcTr1OaB0f3mJBfgWLYKJDzsE.BK8l1YHN0vT0HQyVxEVyb5ffBxCGOaoB39ZJU_O-u-I&dib_tag=se&keywords=dslr&qid=1751577504&sprefix=dsl%2Caps%2C205&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1"
    try:
        driver_manager = DriverManager()
        llm_handler = LLMResponse()
        review_fetcher = ReviewFetcher()
        data_fetcher = DataFetcher()
        driver = driver_manager.get_driver()
        
        # Run the analysis
        markdown_result = llm_handler.run(url, data_fetcher, review_fetcher, driver)

        print("\nReport Generated")
        print(markdown_result)

    except Exception as main_err:
        logger.exception(f"Fatal error during execution: {main_err}")
