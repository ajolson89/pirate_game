import requests
import json
import time
from typing import Dict, Any
from enum import Enum

class TimeOfDay(str, Enum):
    DAWN = "dawn"
    DAY = "day"
    DUSK = "dusk"
    NIGHT = "night"

class Weather(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    FOGGY = "foggy"

def create_test_context(
    character_id: str,
    game_state: str,
    player_message: str,
    time_of_day: TimeOfDay,
    weather: Weather,
    location: str,
    player_location: str
) -> dict:
    return {
        "character_id": character_id,
        "location": location,
        "game_state": game_state,
        "player_location": player_location,
        "player_inventory": {
            "items": {
                "map_piece": True,
                "compass": True,
                "sword": True,
                "gold_coins": True,
                "rum_bottle": False,
                "ancient_artifact": True
            }
        },
        "quest_progress": {
            "active_quest": "find_lost_amulet",
            "quest_stage": 2,
            "completed_quests": ["deliver_message", "clear_rats"]
        },
        "reputation": {
            "pirate_reputation": "neutral",
            "navy_reputation": "friendly",
            "merchant_reputation": "neutral",
            "tribal_reputation": "neutral"
        },
        "time_of_day": time_of_day,
        "weather": weather,
        "npc_state": {
            "is_enemy_aware": False,
            "current_disposition": "friendly",
            "has_traded_today": False,
            "current_wares": []  # Will be populated from NPC background
        },
        "player_message": player_message,
        "treasure_location": "behind_waterfall",
        "game_context": {
            "world_background": """The year is 1742, and the Caribbean is in a state of upheaval. 
            Ancient artifacts of a forgotten civilization have been discovered, promising immense power 
            to those who can collect and decipher them.""",
            
            "main_storyline": """As a skilled navigator, you've discovered that these artifacts, 
            when combined, reveal the location of an ancient city with technology far beyond the current era. 
            You must gather these artifacts while navigating the complex political landscape of the Caribbean.""",
            
            "current_world_state": """Tensions are high as rumors of the artifacts spread. 
            The Navy has increased patrols, pirates are raiding more frequently, merchants are hiring 
            additional guards, and the tribal councils are meeting to discuss their response.""",
            
            "npc_background": None  # Will be populated by the API
        }
    }

def test_npc_dialogue_with_history():
    url = "http://localhost:8000/generate-dialogue"
    
    # Test scenarios for different NPCs
    scenarios = [
        {
            "character_id": "madame_beaufort",
            "location": "the_poop_deck",
            "player_location": "tavern_interior",
            "game_state": "evening_busy",
            "time_of_day": TimeOfDay.NIGHT,
            "weather": Weather.CLEAR,
            "player_message": "Good evening, Madame. I hear you know everything that happens in this port."
        },
        {
            "character_id": "doctor_choppy",
            "location": "the_yellow_jack",
            "player_location": "medical_quarter",
            "game_state": "day_routine",
            "time_of_day": TimeOfDay.DAY,
            "weather": Weather.CLOUDY,
            "player_message": "Doctor, I need treatment for this wound..."
        },
        {
            "character_id": "captain_mutumbe",
            "location": "serpents_haven",
            "player_location": "docks",
            "game_state": "tense_situation",
            "time_of_day": TimeOfDay.DUSK,
            "weather": Weather.STORMY,
            "player_message": "Captain, I seek your counsel about the ancient artifacts."
        },
        {
            "character_id": "itzcoatl",
            "location": "natives_village",
            "player_location": "village_center",
            "game_state": "peaceful_gathering",
            "time_of_day": TimeOfDay.DAWN,
            "weather": Weather.FOGGY,
            "player_message": "Chief Itzcoatl, I come seeking your wisdom about the ancient artifacts."
        },
        {
            "character_id": "necuahual",
            "location": "thieves_landing_outskirts",
            "player_location": "market_edge",
            "game_state": "quiet_afternoon",
            "time_of_day": TimeOfDay.DAY,
            "weather": Weather.CLEAR,
            "player_message": "I noticed you watching the traders. What interests you about them?"
        }
    ]
    
    try:
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*50}")
            print(f"Test Interaction {i}: {scenario['character_id']}")
            print(f"Location: {scenario['location']}")
            print(f"Time: {scenario['time_of_day']}")
            print(f"Weather: {scenario['weather']}")
            print(f"Player Message: {scenario['player_message']}")
            print(f"{'='*50}\n")
            
            # Create full context for the scenario
            context = create_test_context(
                character_id=scenario['character_id'],
                game_state=scenario['game_state'],
                player_message=scenario['player_message'],
                time_of_day=scenario['time_of_day'],
                weather=scenario['weather'],
                location=scenario['location'],
                player_location=scenario['player_location']
            )
            
            # Make the API request
            response = requests.post(url, json=context)
            response.raise_for_status()
            
            result = response.json()
            print("\nNPC Response:")
            print(result['dialogue'])
            
            # Get chat history for this character
            history_response = requests.get(f"http://localhost:8000/chat-history/{scenario['character_id']}")
            history_response.raise_for_status()
            
            print("\nChat History:")
            history = history_response.json()
            print(f"Total interactions: {len(history['conversations'])//2}")  # Divide by 2 because each interaction has user+assistant messages
            
            # Small delay between requests
            time.sleep(2)
        
    except requests.exceptions.RequestException as e:
        print(f"\nError making request: {e}")
        print("Make sure the API server is running on port 8000")

if __name__ == "__main__":
    test_npc_dialogue_with_history() 