import time
from src.common.gui_interactor import GUIInteractor
from src.common.logger import agent_logger as logger
import re

def test_wechat_messages_native():
    """
    Test to verify if we can extract content from the main WeChat message pane
    using pywinauto's native UIA patterns.
    """
    interactor = GUIInteractor()
    logger.info("Connecting to WeChat via control search...")
    
    # Use the robust method: find window by its main navigation bar
    win = interactor.find_window_by_control({"auto_id": "main_tabbar", "control_type": "ToolBar"})
    
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

        # 2. Search for the chat message list
        logger.info("Searching for 'chat_message_list' (Main Message Pane)...")
        # Try finding the specific control you identified
        msg_list = win.child_window(auto_id="chat_message_list", control_type="List")
        
        if not msg_list.exists(timeout=2):
            logger.warning("Could not find 'chat_message_list' by ID. Searching all List controls...")
            lists = win.descendants(control_type="List")
            for l in lists:
                if l.element_info.automation_id == "chat_message_list":
                    msg_list = l
                    break
        
        if not msg_list.exists():
            logger.error("Could not find the message list control.")
            return

        # 3. Extract all messages
        # Individual messages are usually children of the list
        messages = msg_list.children()
        logger.info(f"Found {len(messages)} elements in the message list.")

        print("\n--- WeChat Main Chat History ---\n")
        
        for i, msg in enumerate(messages):
            try:
                # Get the text from the message element. 
                # We prioritize the 'Name' property which often contains the full message text in WeChat
                content = msg.window_text()
                
                # If window_text is empty, look for child text controls
                if not content or len(content) < 2:
                    text_ctrls = msg.descendants(control_type="Text")
                    content = " ".join([t.window_text() for t in text_ctrls if t.window_text()])
                
                if content.strip():
                    # Display without the 'scrambled' formatting
                    clean_content = content.replace('\n', ' ').replace('\r', '').strip()
                    print(f"[{i+1}] {clean_content}")
                
                    # Check for meeting IDs (9-11 digits)
                    meeting_id_match = re.search(r'(\d{3})[- ]?(\d{3})[- ]?(\d{3,4})', clean_content)
                    if meeting_id_match:
                        found_id = "".join(meeting_id_match.groups())
                        if len(found_id) >= 9:
                            print(f"    >>> Meeting ID found: {found_id}")
            except Exception as e:
                continue

        print("\n-----------------------------------\n")

    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_wechat_messages_native()
