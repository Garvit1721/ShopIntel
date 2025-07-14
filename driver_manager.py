# driver_manager.py
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from logger_util import setup_logger

logger = setup_logger(__name__)

class DriverManager:
    def __init__(self):
        self.driver = None
        self.started = False
        self._init_driver()

    def _init_driver(self):
        if self.started:
            return

        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument(f"user-agent={UserAgent().random}")
        options.page_load_strategy = "eager"

        try:
            self.driver = uc.Chrome(options=options, version_main=137)
            self.started = True
            logger.info("Chrome driver started successfully.")
        except Exception as e:
            logger.error(f"Failed to start Chrome driver: {e}")
            self.driver = None
            self.started = False

    def get_driver(self):
        if not self.driver:
            self._init_driver()
        return self.driver

    def shutdown_driver(self):
        if self.driver:
            try:
                logger.info("Shutting down Chrome driver...")
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Driver shutdown error: {e}")
            finally:
                self.driver = None
                self.started = False

    def __del__(self):
        pass 
