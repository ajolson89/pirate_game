# pirate_game

# NPC Dialogue System with LLM Integration

A dynamic NPC (Non-Player Character) dialogue system that generates contextual responses using the Llama 3 language model through Ollama. This system takes into account character backgrounds, game state, player status, and environmental conditions to create immersive and consistent character interactions.

## Features

- **Dynamic NPC Responses**: Generate contextual dialogue based on:
  - Character background and personality
  - Current game state
  - Player inventory and quest progress
  - Time of day and weather
  - Location context
  - Faction reputations
  - Previous interactions

- **Rich Character System**:
  - Detailed character backgrounds stored in JSON
  - Persistent conversation history
  - Reputation tracking
  - Character-specific wares and knowledge

- **FastAPI Integration**:
  - RESTful API endpoints
  - Easy integration with game systems
  - Chat history retrieval
  - Proper error handling

## Prerequisites

- Python 3.8+
- Ollama with Llama 3 model installed
- FastAPI
- Uvicorn

## Installation

1. Clone the repository:
bash
git clone <repository-url>
cd npc-dialogue-system
:
bash
pip install fastapi uvicorn ollama requests
:
bash
ollama pull llama3
npc-dialogue-system/
├── main.py # FastAPI application
├── npc_loader.py # NPC data loading utility
├── test_npc_api.py # Test script
├── npc_backgrounds.json # Character data
└── README.md
:
bash
python main.py
:
bash
python test_npc_api.py
:
http://localhost:8000/docs
:
json
{
"character_id": "madame_beaufort",
"location": "the_poop_deck",
"game_state": "evening_busy",
"player_location": "tavern_interior",
"player_inventory": {
"items": {
"map_piece": true,
"compass": true
}
},
"quest_progress": {
"active_quest": "find_lost_amulet",
"quest_stage": 2,
"completed_quests": ["deliver_message"]
},
"reputation": {
"pirate_reputation": "neutral",
"navy_reputation": "friendly",
"merchant_reputation": "neutral",
"tribal_reputation": "neutral"
},
"time_of_day": "night",
"weather": "clear",
"npc_state": {
"is_enemy_aware": false,
"current_disposition": "friendly",
"has_traded_today": false
},
"player_message": "Good evening, Madame. I hear you know everything that happens in this port."
}
