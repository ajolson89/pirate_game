"""
Test Script for NPC Dialogue Endpoint
Sends test requests to the API and displays responses
"""

import requests
import json
import sys
from typing import Dict
from datetime import datetime
from urllib.parse import urljoin

# Configuration
API_CONFIG = {
    "url": "AWS_URL",  # e.g., "    https://xxxxx.execute-api.region.amazonaws.com/prod/"
    "api_key": "AWS_API_KEY"
}

# Test payload template
TEST_PAYLOAD = {
    "game_id": "test_game_001",
    "character_id": "madame_beaufort",
    "player_message": "Good evening, Madame. I'm looking for a ship and crew.",
    "location": "the_salty_dog_tavern",
    "time_of_day": "evening",
    "weather": "clear",
    "player_location": "tavern_interior",
    "game_state": {
        "potato_quest": "unknown",
        "meat_quest": "unknown",
        "map_quest": "unknown",
        "smuggler_quest": "unknown"
    },
    "reputation": {
        "merchants": "neutral",
        "pirates": "neutral",
        "navy": "neutral",
        "smugglers": "neutral"
    }
}

def save_response(response_data: Dict, character_id: str):
    """Save response to a log file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/dialogue_{character_id}_{timestamp}.json"
    
    # Ensure logs directory exists
    import os
    os.makedirs("logs", exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(response_data, f, indent=2)
    print(f"\nResponse saved to: {filename}")

def test_dialogue(payload: Dict = None):
    """
    Send test request to the dialogue endpoint
    """
    if not payload:
        payload = TEST_PAYLOAD
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_CONFIG["api_key"]
    }
    
    endpoint = urljoin(API_CONFIG["url"].rstrip('/') + '/', 'generate-dialogue')
    
    try:
        print("\nRequest Details:")
        print("-" * 50)
        print(f"Endpoint: {endpoint}")
        print(f"Headers: {json.dumps({k: v[:6] + '...' if k == 'x-api-key' else v for k, v in headers.items()}, indent=2)}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print("-" * 50)
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Raw Response: {response.text}")
        
        print("\nResponse Headers:")
        print(json.dumps(dict(response.headers), indent=2))
        
        if response.status_code == 200:
            response_data = response.json()
            print("\nNPC Response:")
            print("-" * 50)
            print(json.loads(response_data['body'])['dialogue'])
            print("-" * 50)
            
            if 'game_state' in response_data:
                print("\nGame State Changes:")
                print(json.dumps(response_data['game_state'], indent=2))
            
            if 'state_changes' in response_data:
                print("\nDetailed State Changes:")
                print(json.dumps(response_data['state_changes'], indent=2))
            
            # Save response to file
            save_response(response_data, payload['character_id'])
            
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error making request: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")

def load_custom_payload(filename: str) -> Dict:
    """Load a custom payload from a JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading custom payload: {str(e)}")
        return None

def interactive_mode():
    """Interactive mode for testing different messages"""
    payload = TEST_PAYLOAD.copy()
    
    print("\nInteractive NPC Dialogue Test Mode")
    print("-" * 50)
    
    while True:
        print("\nCurrent character:", payload['character_id'])
        print("\nOptions:")
        print("1. Send message")
        print("2. Change character")
        print("3. Change game state")
        print("4. Load custom payload")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ")
        
        if choice == "1":
            message = input("\nEnter your message: ")
            payload['player_message'] = message
            test_dialogue(payload)
        
        elif choice == "2":
            character = input("\nEnter character_id: ")
            payload['character_id'] = character
        
        elif choice == "3":
            print("\nCurrent game state:", json.dumps(payload['game_state'], indent=2))
            quest = input("Enter quest to update: ")
            state = input("Enter new state (unknown/started/complete): ")
            if quest in payload['game_state']:
                payload['game_state'][quest] = state
        
        elif choice == "4":
            filename = input("\nEnter JSON payload filename: ")
            custom_payload = load_custom_payload(filename)
            if custom_payload:
                payload = custom_payload
                print("Custom payload loaded!")
        
        elif choice == "5":
            print("\nExiting...")
            break
        
        else:
            print("\nInvalid option!")

if __name__ == "__main__":
    # First check if API configuration is set
    if API_CONFIG["url"] == "YOUR_API_URL_HERE" or API_CONFIG["api_key"] == "YOUR_API_KEY_HERE":
        print("Error: Please update the API_CONFIG with your actual API URL and key")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_mode()
        else:
            # Load custom payload file if provided
            custom_payload = load_custom_payload(sys.argv[1])
            if custom_payload:
                test_dialogue(custom_payload)
            else:
                print("Using default test payload...")
                test_dialogue()
    else:
        test_dialogue() 