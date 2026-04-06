import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

class IndustryLogger:
    """
    Structured logger that simulates industry practices.
    Logs to both console and a file in JSON format.
    """
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.log_dir = log_dir
        self.current_log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        formatter = logging.Formatter("%(message)s")
        if not any(isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler) for handler in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        if not any(isinstance(handler, logging.FileHandler) for handler in self.logger.handlers):
            self._attach_file_handler(self.current_log_file, formatter, append=True)

    def _attach_file_handler(self, file_path: str, formatter: logging.Formatter, append: bool) -> None:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        file_handler = logging.FileHandler(file_path, mode="a" if append else "w", encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.current_log_file = file_path

    def use_log_file(self, file_path: str, append: bool = True) -> str:
        formatter = logging.Formatter("%(message)s")
        for handler in list(self.logger.handlers):
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
                handler.close()

        self._attach_file_handler(file_path, formatter, append=append)
        return self.current_log_file

    def get_current_log_file(self) -> str:
        return self.current_log_file

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Logs an event with a timestamp and type."""
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        self.logger.info(json.dumps(payload))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)

# Global logger instance
logger = IndustryLogger()
