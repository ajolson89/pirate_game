"""
NPC Dialogue System - AWS Lambda Handler
This module handles NPC dialogue generation using Amazon Bedrock and manages game state.

Key Features:
- Multi-game support with game_id tracking
- Persistent chat history in DynamoDB
- Game state management and transitions
- NPC background loading and context management
- Structured dialogue responses with state changes

Dependencies:
- AWS Bedrock for LLM dialogue generation
- DynamoDB for persistence
- AWS Lambda Powertools for observability
- Custom NPCLoader for character data
"""

from enum import Enum
import json
from typing import Dict, List, Optional
from datetime import datetime
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
import os
from pydantic import BaseModel
from .npc_loader import NPCLoader

# Initialize Powertools
logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

def lambda_handler(event: Dict, context: LambdaContext) -> Dict:
    """
    Lambda handler for NPC dialogue generation
    """
    return app.resolve(event, context)

class QuestState(str, Enum):
    """
    Enumeration of possible quest states
    
    States:
    - UNKNOWN: Quest not yet available or discovered
    - STARTED: Quest is active and in progress
    - COMPLETE: Quest has been completed
    """
    UNKNOWN = "unknown"
    STARTED = "started"
    COMPLETE = "complete"

class GameState(BaseModel):
# class GameState:
    """
    Pydantic model representing the current game state
    Tracks the status of all available quests in the game
    """
    potato_quest: QuestState = QuestState.UNKNOWN
    meat_quest: QuestState = QuestState.UNKNOWN
    map_quest: QuestState = QuestState.UNKNOWN
    smuggler_quest: QuestState = QuestState.UNKNOWN

    class Config:
        """Pydantic model configuration"""
        use_enum_values = True
        extra = "ignore"  # Allow extra fields to be passed without raising an error

class DialogueResponse(BaseModel):
# class DialogueResponse:
    """
    Structured response from NPC dialogue generation
    
    Attributes:
        dialogue: The NPC's verbal response
        game_state: Current state of all quests after interaction
        state_changes: List of specific changes made during interaction
    """
    dialogue: str
    game_state: GameState

class DialogueGenerator:
    """
    Core class handling NPC dialogue generation and game state management
    
    Responsibilities:
    - Loading NPC backgrounds
    - Managing conversation history
    - Generating contextual prompts
    - Processing LLM responses
    - Tracking game state changes
    """
    def __init__(self):
        self.npc_loader = NPCLoader()
        # Initialize AWS clients
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        self.dynamodb = boto3.resource('dynamodb')
        self.chat_history_table = self.dynamodb.Table(os.environ['CHAT_HISTORY_TABLE'])

    def _invoke_bedrock(self, prompt: str) -> str:
        """
        Invoke Bedrock model to generate response
        """
        try:
            body = json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": 500,
                "temperature": 0.7,
                "top_p": 0.9,
            })

            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-v2",
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body.get('completion', '')
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock: {str(e)}")
            raise
    
    def _create_composite_key(self, game_id: str, character_id: str) -> str:
        return f"{game_id}#{character_id}"
    
    def get_chat_history(self, game_id: str, character_id: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve chat history for a specific game and character
        
        Args:
            game_id: The unique identifier for the game session
            character_id: The NPC's identifier
            limit: Maximum number of history items to return
            
        Returns:
            List of previous interactions
        """
        try:
            composite_key = self._create_composite_key(game_id, character_id)
            
            response = self.chat_history_table.query(
                KeyConditionExpression='composite_key = :key',
                ExpressionAttributeValues={
                    ':key': composite_key
                },
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            history = response.get('Items', [])
            history.reverse()  # Chronological order
            
            logger.info(f"Retrieved {len(history)} chat history items for {composite_key}")
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {str(e)}")
            return []
    
    def store_interaction(self, game_id: str, character_id: str, context: Dict, response: Dict):
        """
        Store an interaction in the chat history
        
        Args:
            game_id: The unique identifier for the game session
            character_id: The NPC's identifier
            context: The request context
            response: The generated response
        """
        try:
            composite_key = self._create_composite_key(game_id, character_id)
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'composite_key': composite_key,
                'timestamp': timestamp,
                'game_id': game_id,
                'character_id': character_id,
                'context': context,
                'response': response,
                'ttl': int((datetime.utcnow().timestamp() + (30 * 24 * 60 * 60)))  # 30 days TTL
            }
            
            self.chat_history_table.put_item(Item=item)
            logger.info(f"Stored interaction for {composite_key}")
            
        except Exception as e:
            logger.error(f"Error storing interaction: {str(e)}")
            raise
    
    def synthesize_conversation_history(self, history: List[Dict]) -> str:
        """Convert chat history into a contextual summary"""
        if not history:
            return ""
            
        summary = []
        for entry in history:
            player_msg = entry['context']['player_message']
            npc_response = entry['response']
            summary.append(f"Player: {player_msg}\nNPC: {npc_response}")
        
        return "\n\nPrevious conversation:\n" + "\n".join(summary[-3:])  # Last 3 interactions

    @tracer.capture_method
    def generate_prompt(self, context: Dict) -> str:
        try:
            # Load NPC background
            character = context['character_id']
            print(f'Attempting to load NPC background: {character}')
            npc_background = self.npc_loader.get_npc_background(character)
            if not npc_background:
                logger.warning(f"No background found for character: {character}")
                npc_background = "Default NPC background"

            # Get conversation history
            history = self.get_chat_history(
                game_id=context['game_id'],
                character_id=context['character_id']
            )
            conversation_context = self.synthesize_conversation_history(history)

            # Format game state for prompt
            game_state_context = "\n".join([
                f"- {quest}: {state}"
                for quest, state in context['game_state'].items()
            ])

            prompt = f"""You are an NPC named {context['character_id']} with the following background:
{npc_background}

Current game state:
{game_state_context}

Character location: {context.get('location', 'unknown')}
Time of day: {context.get('time_of_day', 'unknown')}
Weather: {context.get('weather', 'unknown')}

Player status:
- Location: {context.get('player_location', 'unknown')}
- Reputation: {json.dumps(context.get('reputation', {}), indent=2)}
{conversation_context}

Player says: {context.get('player_message', '')}

Respond in two parts:
1. DIALOGUE: Your in-character response
2. GAME_STATE: Same format as the request game state with any modifications based on context of the interaction

Available game states are:
- potato_quest: {QuestState.UNKNOWN.value}/{QuestState.STARTED.value}/{QuestState.COMPLETE.value}
- meat_quest: {QuestState.UNKNOWN.value}/{QuestState.STARTED.value}/{QuestState.COMPLETE.value}
- map_quest: {QuestState.UNKNOWN.value}/{QuestState.STARTED.value}/{QuestState.COMPLETE.value}
- smuggler_quest: {QuestState.UNKNOWN.value}/{QuestState.STARTED.value}/{QuestState.COMPLETE.value}

Format your response as:
DIALOGUE: [Your in-character response]
GAME_STATE: [Same format as the request game state with any modifications based on context of the interaction]
"""
            print(prompt)
            return prompt

        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}")
            raise

    def parse_response(self, response_text: str, current_game_state: Dict) -> DialogueResponse:
        """Parse LLM response into dialogue and state changes"""
        try:
            parts = response_text.split('STATE_CHANGES:')
            dialogue = parts[0].replace('DIALOGUE:', '').strip()
            
            # Start with current game state
            new_game_state = GameState(**current_game_state)
            state_changes = []
            
            if len(parts) > 1:
                changes_text = parts[1].strip()
                for change in changes_text.split('-')[1:]:
                    try:
                        lines = change.strip().split('\n')
                        change_dict = {}
                        for line in lines:
                            if ':' in line:
                                key, value = line.split(':', 1)
                                change_dict[key.strip()] = value.strip()
                        
                        if 'QUEST' in change_dict and 'NEW_STATE' in change_dict:
                            quest_name = change_dict['QUEST'].lower()
                            new_state = change_dict['NEW_STATE'].lower()
                            if hasattr(new_game_state, quest_name) and new_state in QuestState.__members__:
                                setattr(new_game_state, quest_name, QuestState(new_state))
                                state_changes.append({
                                    'quest': quest_name,
                                    'old_state': current_game_state.get(quest_name, QuestState.UNKNOWN),
                                    'new_state': new_state,
                                    'reason': change_dict.get('REASON', 'No reason provided')
                                })
                    
                    except Exception as e:
                        logger.warning(f"Error parsing state change: {str(e)}")
                        continue
                dialogue = dialogue.split('GAME_STATE:')[0].strip()
            return DialogueResponse(
                dialogue=dialogue,
                game_state=new_game_state,
                state_changes=state_changes
            )
            
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return DialogueResponse(
                dialogue=response_text,
                game_state=GameState(**current_game_state)
            )

    @tracer.capture_method
    def generate_dialogue(self, context: Dict) -> DialogueResponse:
        print('Generating dialogue')
        print(context)
        try:
            prompt = self.generate_prompt(context)
            
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-v2',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            response_body = json.loads(response.get('body').read())

            response_body = response_body.get('content', '')
            response_text = response_body[0]['text']

            parsed_response = self.parse_response(response_text, context['game_state'])

            return parsed_response
            
        except Exception as e:
            logger.error(f"Error generating dialogue: {str(e)}")
            raise

# Initialize the dialogue generator
dialogue_generator = DialogueGenerator()

@app.post("/generate-dialogue")
@tracer.capture_method
def handle_dialogue_generation():
    try:
        print('Handling dialogue generation')
        logger.info("Received dialogue generation request")
        context = app.current_event.json_body
        logger.info(f"Request context: {json.dumps(context)}")
        
        # Validate required fields
        required_fields = ['game_id', 'character_id', 'player_message', 'game_state']
        missing_fields = [field for field in required_fields if field not in context]
        
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"Missing required fields: {missing_fields}"
                })
            }
        
        logger.info("Generating dialogue response")
        response = dialogue_generator.generate_dialogue(context)
        logger.info("Dialogue generated successfully")
        print(response.dict())
        
        # Store interaction
        try:
            dialogue_generator.store_interaction(
                game_id=context['game_id'],
                character_id=context['character_id'],
                context=context,
                response=response.dict()
            )
            logger.info("Interaction stored successfully")
        except Exception as store_error:
            logger.error(f"Error storing interaction: {str(store_error)}")
            # Continue even if storage fails
        
        return {
            "statusCode": 200,
            "body": json.dumps(response.dict())
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e),
                "type": type(e).__name__
            })
        }