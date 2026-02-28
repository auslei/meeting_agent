import time
import re
from typing import Optional, Dict, Iterator
from src.common.logger import agent_logger as logger
from src.common.gui_interactor import GUIInteractor

class WeChatWatcher:
    """
    Monitors WeChat for meeting-related messages.
    Scans both the chat list (native snippets) and the main chat pane (OCR).
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
        """Find the WeChat window using pywinauto by looking for its main tab bar."""
        # We search for a window that contains the 'main_tabbar' Toolbar
        # This is more robust than searching by title if the title is empty.
        win = self.interactor.find_window_by_control({"auto_id": "main_tabbar", "control_type": "ToolBar"})
        if not win:
            # Fallback to title search if control search fails
            win = self.interactor.find_window_native(r".*(WeChat|微信).*")
        return win

    def scan_chat_list(self, win) -> Optional[str]:
        """Natively scan the chat list (sidebar) for meeting IDs in snippets."""
        try:
            # The chat list is a ListBox with auto_id 'session_list'
            chat_list = win.child_window(auto_id="session_list", control_type="List")
            if chat_list.exists():
                items = chat_list.children(control_type="ListItem")
                for item in items:
                    name = item.window_text()
                    logger.debug(f"Checking chat list item: {name}")
                    for pattern in self.meeting_patterns:
                        match = re.search(pattern, name)
                        if match:
                            meeting_id = "".join(match.groups()) if match.groups()[0] else match.group(0)
                            # Clean ID (remove non-digits)
                            meeting_id = re.sub(r"\D", "", meeting_id)
                            return meeting_id
        except Exception as e:
            logger.debug(f"Native chat list scan failed: {e}")
        return None

    def scan_chat_pane(self, win) -> Optional[str]:
        """Scan the main chat pane using targeted OCR."""
        try:
            # Get the window rectangle
            rect = win.rectangle()
            width = rect.width()
            height = rect.height()
            
            # Based on user discovery: Content area is the right side
            # L706 is the start of the chat list, so everything to the right is the pane
            # We use a safe margin to target the message area (X=1128 from user discovery)
            content_x = max(int(rect.left + (width * 0.35)), 1100) 
            content_width = int(rect.right - content_x)
            
            # Focus on the middle-to-bottom area where new messages appear
            region = (content_x, int(rect.top + 100), content_width, int(height - 200))
            
            text = self.interactor.ocr_region(region, debug_name="wechat_chat_pane")
            logger.debug(f"Pane OCR Result Length: {len(text)}")

            for pattern in self.meeting_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    for match in matches:
                        meeting_id = "".join(match) if isinstance(match, tuple) else match
                        meeting_id = re.sub(r"\D", "", meeting_id)
                        if meeting_id:
                            return meeting_id
        except Exception as e:
            logger.error(f"Chat pane scan failed: {e}")
        return None

    def scan_for_meeting_info(self) -> Optional[Dict[str, str]]:
        """Orchestrate the scanning of WeChat."""
        win = self.find_wechat_window_native()
        if not win:
            return None

        # 1. Try native chat list scan (Fast, background-friendly)
        meeting_id = self.scan_chat_list(win)
        
        # 2. If not found, try targeted OCR on the main pane
        if not meeting_id:
            # We only bring to front for OCR to ensure visibility
            win.set_focus()
            time.sleep(0.5)
            meeting_id = self.scan_chat_pane(win)

        if meeting_id and meeting_id != self.last_meeting_id:
            logger.info(f"Detected new meeting ID: {meeting_id}")
            self.last_meeting_id = meeting_id
            return {"type": "id_or_code", "value": meeting_id}
            
        return None

    def watch(self, interval: int = 10) -> Iterator[Dict[str, str]]:
        """Start polling WeChat."""
        logger.info(f"Starting WeChat watcher (polling every {interval}s)...")
        while True:
            result = self.scan_for_meeting_info()
            if result:
                yield result
            time.sleep(interval)
