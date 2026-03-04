import time
import sys
import os
import argparse
from src.common.logger import agent_logger as logger
from src.common.gui_interactor import GUIInteractor
from src.wemeet.joiner import WeMeetJoiner

def test_join_flow(meeting_id: str):
    logger.info(f"--- Starting E2E Test for WeMeet Join Flow ---")
    logger.info(f"Target Meeting ID: {meeting_id}")
    
    interactor = GUIInteractor()
    joiner = WeMeetJoiner(interactor)
    
    # 1. Start Tencent Meeting / Join
    logger.info("Attempting to join via GUI...")
    success = joiner.join_via_gui(meeting_id)
    
    if not success:
        logger.error("Failed to join the meeting via GUI. Test failed.")
        sys.exit(1)
        
    logger.info("SUCCESS: Successfully initiated join sequence!")
    
    # 2. Wait for meeting to complete
    logger.info("Waiting for meeting to complete. We will poll the window status...")
    logger.info("(You can manually close the Tencent Meeting window to simulate meeting end)")
    
    poll_interval = 10
    start_time = time.time()
    
    while True:
        # Check if the meeting window is still active
        is_active = joiner.verify_in_meeting()
        if not is_active:
            logger.info("Meeting window is no longer detected. Meeting has ended.")
            break
            
        elapsed = int(time.time() - start_time)
        logger.debug(f"Meeting still active. Elapsed time: {elapsed} seconds. Sleeping for {poll_interval}s...")
        time.sleep(poll_interval)
        
    logger.info("--- E2E Test Completed Successfully ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test WeMeet Join Flow End-to-End")
    parser.add_argument("--id", type=str, default="123456789", help="The Meeting ID to test with.")
    args = parser.parse_args()
    
    try:
        test_join_flow(args.id)
    except KeyboardInterrupt:
        logger.info("Test aborted by user.")
