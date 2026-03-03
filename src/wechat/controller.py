import time
import subprocess
import os
import re
from typing import Optional, List, Dict
from src.common.logger import agent_logger as logger

try:
    from pywinauto import Application, Desktop
    from pywinauto.keyboard import send_keys
except ImportError:
    logger.warning("pywinauto is not installed or not available on this OS.")

class WeChatController:
    """
    Library for automating WeChat interactions on Windows using PyWinAuto.
    """
    def __init__(self):
        self.desktop = Desktop(backend="uia")
        self.wechat_path = r"C:\Program Files\Tencent\Weixin\Weixin.exe"

    def _find_window(self):
        """Find the main WeChat window."""
        # Preferred: Look for the 'main_tabbar'
        for win in self.desktop.windows():
            try:
                # Need to use WindowSpecification for child_window access
                win_spec = self.desktop.window(handle=win.handle)
                if win_spec.child_window(auto_id="main_tabbar", control_type="ToolBar").exists(timeout=0.1):
                    return win_spec
            except:
                pass
        
        # Fallback: Title search
        windows = self.desktop.windows(title_re=r".*(WeChat|微信).*")
        if windows:
            return self.desktop.window(handle=windows[0].handle)
            
        return None

    def start_wechat(self) -> bool:
        """
        Start WeChat if not running, and bring it to foreground.
        Returns True if WeChat is ready to use.
        """
        win = self._find_window()
        if win:
            logger.info("WeChat is already running. Focusing...")
            win.set_focus()
            return True

        if not os.path.exists(self.wechat_path):
            logger.error(f"WeChat executable not found at: {self.wechat_path}")
            return False

        logger.info(f"Launching WeChat from: {self.wechat_path}")
        try:
            subprocess.Popen([self.wechat_path], start_new_session=True)
            logger.info("Waiting for WeChat window...")
            
            for _ in range(15):
                time.sleep(1)
                win = self._find_window()
                if win:
                    logger.info("WeChat launched successfully.")
                    win.set_focus()
                    return True
                    
            logger.error("WeChat launched but window did not appear.")
            return False
        except Exception as e:
            logger.error(f"Failed to launch WeChat: {e}")
            return False

    def search_chat(self, chat_name: str) -> bool:
        """
        Search for a specific chat by name and open it.
        """
        win = self._find_window()
        if not win:
            logger.error("WeChat window not found.")
            return False
            
        try:
            win.set_focus()
            time.sleep(0.5)

            # Ctrl+F to focus search
            send_keys("^f")
            time.sleep(0.5)

            # Find search box to type (if Ctrl+F failed to focus it)
            search_box = win.child_window(title="Search", control_type="Edit")
            if not search_box.exists(timeout=1):
                edits = win.descendants(control_type="Edit")
                if edits:
                    search_box = min(edits, key=lambda e: (e.rectangle().top, e.rectangle().left))
                else:
                    logger.error("Search box not found.")
                    return False

            search_box.click_input()
            search_box.type_keys("^a{BACKSPACE}", with_spaces=True)
            time.sleep(0.5)
            search_box.type_keys(chat_name, with_spaces=True)
            time.sleep(1.5) # Wait for search results
            
            found = False
            results = win.descendants(control_type="ListItem")
            for item in results:
                try:
                    if chat_name.lower() in item.window_text().lower():
                        item.click_input()
                        time.sleep(1)
                        found = True
                        break
                except:
                    continue
                    
            if not found:
                # Press enter as fallback
                send_keys("{ENTER}")
                time.sleep(1)
                
            return True
        except Exception as e:
            logger.error(f"Failed to search chat '{chat_name}': {e}")
            return False

    def get_messages(self, limit: int = 50) -> List[str]:
        """
        Get the most recent messages from the currently open chat.
        """
        win = self._find_window()
        if not win:
            logger.error("WeChat window not found.")
            return []
            
        try:
            win.set_focus()
            time.sleep(0.5)

            msg_list = win.child_window(auto_id="chat_message_list", control_type="List")
            if not msg_list.exists(timeout=2):
                lists = win.descendants(control_type="List")
                if lists:
                    # Usually the list on the right is the message list
                    msg_list = max(lists, key=lambda l: l.rectangle().left)
                else:
                    return []

            items = msg_list.children()
            messages = []
            
            for item in items[-limit:]: # Only process up to 'limit' items from the end
                try:
                    content = item.window_text()
                    if not content or len(content) < 2:
                        text_ctrls = item.descendants(control_type="Text")
                        content = " ".join([t.window_text() for t in text_ctrls if t.window_text()])
                    
                    if content and content.strip():
                        clean_content = " ".join(content.split())
                        messages.append(clean_content)
                except:
                    continue
                    
            return messages
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []

    def get_chat_list(self) -> List[str]:
        """
        Get the list of recent chats from the sidebar.
        """
        win = self._find_window()
        if not win:
            logger.error("WeChat window not found.")
            return []
            
        try:
            win.set_focus()
            time.sleep(0.5)

            chat_list = win.child_window(auto_id="session_list", control_type="List")
            if not chat_list.exists(timeout=2):
                return []
                
            items = chat_list.children(control_type="ListItem")
            chats = []
            for item in items:
                try:
                    name = item.window_text()
                    if name:
                        chats.append(name)
                except:
                    continue
            return chats
        except Exception as e:
            logger.error(f"Failed to get chat list: {e}")
            return []

    def extract_meeting_ids(self, text: str) -> List[str]:
        """Utility to extract WeMeet IDs from text."""
        patterns = [
            r'(?:腾讯会议|BRS|RAS|RAKES|会议|Meeting)[:：]?\s?(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})',
            r'(?:腾讯会议|BRS|RAS|RAKES|会议|Meeting)[:：]?\s?(\d{9,10})',
            r'(?:\s|^)(\d{3})[- ](\d{3})[- ](\d{3,4})(?:\s|$)'
        ]
        
        found_ids = set()
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.groups():
                    meeting_id = "".join(match.groups()) if match.groups()[0] else match.group(0)
                else:
                    meeting_id = match.group(0)
                meeting_id = re.sub(r"\D", "", meeting_id)
                if len(meeting_id) >= 9:
                    found_ids.add(meeting_id)
                    
        return list(found_ids)
