import time
import re
from src.common.gui_interactor import GUIInteractor
from src.common.logger import agent_logger as logger

def test_wechat_search_and_extract(chat_name: str = "Mom Gao"):
    """
    1. Search for a specific chat.
    2. Extract its message history.
    """
    interactor = GUIInteractor()
    
    # 1. Search for the chat
    logger.info(f"Step 1: Searching for chat '{chat_name}'...")
    if not interactor.search_wechat_chat(chat_name):
        logger.error(f"Failed to find or open chat '{chat_name}'")
        return

    # 2. Wait for the chat pane to load
    time.sleep(2)

    # 3. Connect to WeChat window again to ensure we have the latest UIA tree
    win = interactor.find_window_by_control({"auto_id": "main_tabbar", "control_type": "ToolBar"})
    if not win:
        win = interactor.find_window_native(r".*(WeChat|微信).*")
    
    if not win:
        logger.error("Could not reconnect to WeChat window.")
        return

    # 4. Extract messages from 'chat_message_list'
    logger.info(f"Step 2: Extracting messages from '{chat_name}'...")
    try:
        msg_list = win.child_window(auto_id="chat_message_list", control_type="List")
        
        if not msg_list.exists(timeout=3):
            # Fallback: look for any List on the right
            lists = win.descendants(control_type="List")
            if lists:
                msg_list = max(lists, key=lambda l: l.rectangle().left)
            else:
                logger.error("Could not find message list control.")
                return

        items = msg_list.children()
        print(f"\n--- Chat History: {chat_name} ---\n")
        
        for i, item in enumerate(items):
            try:
                content = item.window_text()
                if not content:
                    text_elements = item.descendants(control_type="Text")
                    content = " ".join([t.window_text() for t in text_elements if t.window_text()])
                
                if content.strip():
                    clean_text = " ".join(content.split())
                    print(f"[{i+1}] {clean_text}")
                    
                    # Optional: Detect Meeting IDs
                    match = re.search(r'(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})', clean_text)
                    if match:
                        found_id = "".join(match.groups())
                        if len(found_id) >= 9:
                            print(f"    >>> Meeting ID detected: {found_id}")
            except:
                continue
        
        print("\n-----------------------------------\n")

    except Exception as e:
        logger.error(f"Extraction failed: {e}")

if __name__ == "__main__":
    # You can change the name here to test different chats
    test_wechat_search_and_extract("Mom Gao")
