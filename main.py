import ollama


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from npc_loader import NPCLoader

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

class ReputationLevel(str, Enum):
    HOSTILE = "hostile"
    LOW = "low"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    HIGH = "high"

class PlayerInventory(BaseModel):
    items: Dict[str, bool]

class QuestProgress(BaseModel):
    active_quest: Optional[str]
    quest_stage: Optional[int]
    completed_quests: List[str] = []

class Reputation(BaseModel):
    pirate_reputation: ReputationLevel
    navy_reputation: ReputationLevel
    merchant_reputation: ReputationLevel
    tribal_reputation: ReputationLevel

class NPCState(BaseModel):
    is_enemy_aware: bool
    current_disposition: str
    has_traded_today: bool = False
    current_wares: List[str] = []

class GameContext(BaseModel):
    world_background: str
    main_storyline: str
    current_world_state: str
    npc_background: Optional[str] = None

class NPCContext(BaseModel):
    character_id: str
    location: str
    game_state: str
    player_location: str
    player_inventory: PlayerInventory
    quest_progress: QuestProgress
    reputation: Reputation
    time_of_day: TimeOfDay
    weather: Weather
    npc_state: NPCState
    player_message: str
    treasure_location: Optional[str] = None
    game_context: GameContext

class ChatHistory:
    def __init__(self):
        self.conversations: Dict[str, List[dict]] = {}
        self.reputation_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_interaction(self, character_id: str, user_content: str, assistant_content: str, reputation: Reputation):
        if character_id not in self.conversations:
            self.conversations[character_id] = []
            self.reputation_history[character_id] = []
        
        timestamp = datetime.now().isoformat()
        
        # Store the interaction
        self.conversations[character_id].extend([
            {"role": "user", "content": user_content, "timestamp": timestamp},
            {"role": "assistant", "content": assistant_content, "timestamp": timestamp}
        ])
        
        # Store reputation at time of interaction
        self.reputation_history[character_id].append({
            "timestamp": timestamp,
            "reputation": reputation.dict()
        })
    
    def get_recent_history(self, character_id: str, max_messages: int = 10) -> List[dict]:
        if character_id not in self.conversations:
            return []
        
        recent_messages = self.conversations[character_id][-max_messages:]
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]

app = FastAPI()
chat_history = ChatHistory()

# Initialize the NPC loader
npc_loader = NPCLoader()

def generate_prompt(context: NPCContext) -> str:
    """Generate a structured prompt for the LLM based on the NPC context."""
    prompt = f"""Game World Context:
{context.game_context.world_background}

Main Story:
{context.game_context.main_storyline}

Current World State:
{context.game_context.current_world_state}

NPC Background:
{context.game_context.npc_background or 'Standard NPC background'}

You are an NPC in a video game with ID: {context.character_id}.
Location: {context.location}
Game State: {context.game_state}
Time: {context.time_of_day}
Weather: {context.weather}

Player Context:
- Location: {context.player_location}
- Items: {', '.join(k for k, v in context.player_inventory.items.items() if v)}
- Active Quest: {context.quest_progress.active_quest or 'None'} (Stage: {context.quest_progress.quest_stage or 0})
- Completed Quests: {', '.join(context.quest_progress.completed_quests)}

Reputation Status:
- Pirates: {context.reputation.pirate_reputation}
- Navy: {context.reputation.navy_reputation}
- Merchants: {context.reputation.merchant_reputation}
- Tribes: {context.reputation.tribal_reputation}

NPC State:
- Enemy Aware: {context.npc_state.is_enemy_aware}
- Disposition: {context.npc_state.current_disposition}
- Has Traded Today: {context.npc_state.has_traded_today}
- Available Wares: {', '.join(context.npc_state.current_wares)}

Player says: {context.player_message}

Based on this context and our previous interactions, generate a natural and engaging response that fits within the game world and story context. Keep the response concise and relevant."""
    
    if context.treasure_location:
        prompt += f"\n\nNote: There is treasure buried in: {context.treasure_location}"
    
    return prompt

@app.post("/generate-dialogue")
async def generate_dialogue(context: NPCContext):
    try:
        # Get NPC background
        npc_background = npc_loader.get_npc_background(context.character_id)
        if npc_background:
            context.game_context.npc_background = npc_background
        
        # Update NPC state with default wares if none specified
        if not context.npc_state.current_wares:
            context.npc_state.current_wares = npc_loader.get_npc_wares(context.character_id)
        
        prompt = generate_prompt(context)
        
        messages = [
            {"role": "system", "content": "You are a video game NPC. Provide short, natural responses that reflect the current reputation levels and maintain character consistency."}
        ]
        
        messages.extend(chat_history.get_recent_history(context.character_id))
        messages.append({"role": "user", "content": prompt})
        
        response = ollama.chat(
            model="llama3",
            messages=messages
        )
        
        npc_dialogue = response['message']['content']
        
        chat_history.add_interaction(
            character_id=context.character_id,
            user_content=context.player_message,
            assistant_content=npc_dialogue,
            reputation=context.reputation
        )
        
        return {"dialogue": npc_dialogue}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat-history/{character_id}")
async def get_character_history(character_id: str):
    """Endpoint to retrieve chat history and reputation history for a specific character"""
    conversations = chat_history.conversations.get(character_id, [])
    reputation_history = chat_history.reputation_history.get(character_id, [])
    return {
        "character_id": character_id,
        "conversations": conversations,
        "reputation_history": reputation_history
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
