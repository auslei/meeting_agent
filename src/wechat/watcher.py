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
            # Standard pattern
            r'腾讯会议[:：]\s?(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})',
            r'腾讯会议[:：]\s?(\d{9,10})',
            # Fallback for OCR misidentifications (like BRS or RAS)
            r'(?:BRS|RAS|RAKES)[:：]?\s?(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})',
            r'(?:BRS|RAS|RAKES)[:：]?\s?(\d{9,10})'
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
            # WeChat layout: Sidebar (~70px), Chat List (~250px), Chat Content (the rest)
            # We target the right 70% of the window to focus on messages
            width = int(box.width)
            content_x = int(box.left + (width * 0.3)) 
            content_width = int(width * 0.7)
            
            region = (content_x, int(box.top), content_width, int(box.height))
            
            text = self.interactor.ocr_region(region, debug_name="wechat_chat_pane")
            logger.debug(f"Targeted OCR Text: {text}")

            # Broaden matching: look for the 9-10 digit pattern even with noisy prefixes
            # We allow common OCR errors for "腾讯会议" or just the ID if it's in a clean line
            flexible_patterns = [
                # Standard or misread prefixes
                r'(?:腾讯会议|BRS|RAS|RAKES|会议)[:：]?\s?(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})',
                r'(?:腾讯会议|BRS|RAS|RAKES|会议)[:：]?\s?(\d{9,10})',
                # Pure IDs that look like meeting IDs (3-3-3 pattern)
                r'(?:\s|^)(\d{3})[- ](\d{3})[- ](\d{3,4})(?:\s|$)'
            ]

            for pattern in flexible_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    # matches can be a list of tuples (for capturing groups)
                    for match in matches:
                        if isinstance(match, tuple):
                            meeting_id = "".join(match)
                        else:
                            meeting_id = match
                        
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
