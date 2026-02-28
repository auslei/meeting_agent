import time
import re
from typing import Optional, Dict, Iterator
from src.common.logger import agent_logger as logger
from src.common.gui_interactor import GUIInteractor

class WeChatWatcher:
    """
    Monitors WeChat for meeting-related messages using native focus and targeted OCR.
    """
    def __init__(self, interactor: GUIInteractor):
        self.interactor = interactor
        self.last_meeting_id: Optional[str] = None
        # We allow common OCR errors for "腾讯会议" or just the ID patterns
        self.meeting_patterns = [
            r'(?:腾讯会议|BRS|RAS|RAKES|会议|Meeting)[:：]?\s?(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})',
            r'(?:腾讯会议|BRS|RAS|RAKES|会议|Meeting)[:：]?\s?(\d{9,10})',
            r'(?:\s|^)(\d{3})[- ](\d{3})[- ](\d{3,4})(?:\s|$)'
        ]

    def find_wechat_window_native(self):
        """Find and focus the WeChat window using pywinauto."""
        return self.interactor.find_window_native(r".*(WeChat|微信).*")

    def scan_for_meeting_info(self) -> Optional[Dict[str, str]]:
        """Scan the WeChat window for meeting IDs using targeted OCR."""
        win = self.find_wechat_window_native()
        if not win:
            logger.warning("WeChat window not found natively.")
            return None

        try:
            # Activate window to ensure it's on top
            win.set_focus()
            time.sleep(0.5) 

            # Get the window rectangle (L, T, R, B)
            rect = win.rectangle()
            width = rect.width()
            height = rect.height()
            
            # WeChat layout: Content area is roughly the right 70% of the window
            # We target this area to avoid sidebar noise
            content_x = int(rect.left + (width * 0.3)) 
            content_width = int(width * 0.7)
            
            region = (content_x, int(rect.top), content_width, int(height))
            
            text = self.interactor.ocr_region(region, debug_name="wechat_chat_pane")
            logger.debug(f"Targeted OCR Text Length: {len(text)}")

            for pattern in self.meeting_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    for match in matches:
                        meeting_id = "".join(match) if isinstance(match, tuple) else match
                        
                        if meeting_id != self.last_meeting_id:
                            logger.info(f"Detected potential meeting ID: {meeting_id}")
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
