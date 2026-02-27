import time
import re
from typing import Optional, Dict, Iterator
from src.common.logger import agent_logger as logger
from src.common.gui_interactor import GUIInteractor

class WeChatWatcher:
    """
    Monitors WeChat for meeting-related messages.
    """
    def __init__(self, interactor: GUIInteractor):
        self.interactor = interactor
        self.last_meeting_id: Optional[str] = None
        self.meeting_patterns = [
            r'腾讯会议[:：]\s?(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})',
            r'腾讯会议[:：]\s?(\d{9,10})'
        ]

    def find_wechat_window(self):
        """Find and focus the WeChat window."""
        win = self.interactor.find_window(["WeChat", "微信"])
        if win:
            logger.info("Found WeChat window.")
            return win
        return None

    def scan_for_meeting_info(self) -> Optional[Dict[str, str]]:
        """Scan the WeChat window for meeting IDs or links."""
        win = self.find_wechat_window()
        if not win:
            logger.warning("WeChat window not found. Please ensure it is open.")
            return None

        try:
            box = win.box
            region = (int(box.left), int(box.top), int(box.width), int(box.height))
            text = self.interactor.ocr_region(region)
            logger.debug(f"OCR Text: {text}")

            for pattern in self.meeting_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    if isinstance(matches[0], tuple):
                        meeting_id = "".join(matches[0])
                    else:
                        meeting_id = matches[0]
                    
                    if meeting_id != self.last_meeting_id:
                        logger.info(f"Detected new meeting info: {meeting_id}")
                        self.last_meeting_id = meeting_id
                        return {"type": "id_or_code", "value": meeting_id}

        except Exception as e:
            logger.error(f"Error during WeChat scan: {e}")
            
        return None

    def watch(self, interval: int = 10) -> Iterator[Dict[str, str]]:
        """Start polling WeChat."""
        logger.info(f"Starting WeChat watcher (polling every {interval}s)...")
        while True:
            result = self.scan_for_meeting_info()
            if result:
                yield result
            time.sleep(interval)
