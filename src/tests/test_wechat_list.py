import time
from src.common.gui_interactor import GUIInteractor
from src.common.logger import agent_logger as logger
import re

def test_wechat_list_native():
    """
    Test to verify if we can extract all content from the WeChat message list
    using pywinauto's native UIA patterns.
    """
    interactor = GUIInteractor()
    logger.info("Connecting to WeChat via control search...")
    
    # We look for a window that contains the 'WeChat' button in the navigation bar
    win = interactor.find_window_by_control({"title": "WeChat", "control_type": "Button"})
    
    if not win:
        logger.warning("Could not find WeChat via control. Falling back to title search...")
        win = interactor.find_window_native(r".*(WeChat|微信).*")

    if not win:
        logger.error("WeChat window not found. Please ensure WeChat is open.")
        return

    try:
        # 1. Focus the window
        win.set_focus()
        time.sleep(1)

        # 2. Find all List controls
        logger.info("Scanning for List controls...")
        lists = win.descendants(control_type="List")
        
        # We want the 'chat_message_list' which is typically on the right (larger X)
        # and has many children.
        chat_list = None
        for l in lists:
            auto_id = l.element_info.automation_id
            if auto_id == "chat_message_list":
                chat_list = l
                logger.info("Found 'chat_message_list' by ID.")
                break
        
        if not chat_list and lists:
            # Fallback: Pick the list furthest to the right
            chat_list = max(lists, key=lambda l: l.rectangle().left)
            logger.info(f"Using fallback list at X={chat_list.rectangle().left}")

        if not chat_list:
            logger.error("Could not find any message list in the window.")
            return

        # 3. Extract all items (messages)
        items = chat_list.children()
        logger.info(f"Found {len(items)} items in the chat list.")

        print("\n--- WeChat Message History (Cleaned) ---\n")
        
        for i, item in enumerate(items):
            try:
                # Get text from the 'Name' property or children
                content = item.window_text()
                if not content:
                    # Look for Text children (common for message bubbles)
                    text_elements = item.descendants(control_type="Text")
                    content = " ".join([t.window_text() for t in text_elements if t.window_text()])
                
                if content.strip():
                    # Remove any newlines or excess whitespace
                    clean_text = " ".join(content.split())
                    print(f"[{i+1}] {clean_text}")
                    
                    # Check for meeting ID
                    match = re.search(r'(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})', clean_text)
                    if match:
                        found_id = "".join(match.groups())
                        if len(found_id) >= 9:
                            print(f"    >>> Meeting ID detected: {found_id}")
            except:
                continue

        print("\n-----------------------------------\n")

    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_wechat_list_native()
