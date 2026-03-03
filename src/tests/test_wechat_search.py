import time
from src.wechat import WeChatController
from src.common.logger import agent_logger as logger

def test_wechat_search_and_extract(chat_name: str = "Mom Gao"):
    """
    1. Search for a specific chat.
    2. Extract its message history.
    """
    controller = WeChatController()
    
    # 1. Search for the chat
    logger.info(f"Step 1: Searching for chat '{chat_name}'...")
    if not controller.search_chat(chat_name):
        logger.error(f"Failed to find or open chat '{chat_name}'")
        return

    # 2. Wait for the chat pane to load
    time.sleep(2)

    # 3. Extract messages
    logger.info(f"Step 2: Extracting messages from '{chat_name}'...")
    messages = controller.get_messages(limit=20)
    
    if not messages:
        logger.error(f"No messages retrieved from '{chat_name}'.")
        return
        
    print(f"\n--- Chat History: {chat_name} ---\n")
    
    for i, msg in enumerate(messages):
        print(f"[{i+1}] {msg}")
        
        # Optional: Detect Meeting IDs
        ids = controller.extract_meeting_ids(msg)
        for meeting_id in ids:
            print(f"    >>> Meeting ID detected: {meeting_id}")
            
    print("\n-----------------------------------\n")

if __name__ == "__main__":
    # You can change the name here to test different chats
    test_wechat_search_and_extract("Mom Gao")
