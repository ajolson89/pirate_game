import json
from typing import Dict, Any, Optional

class NPCLoader:
    def __init__(self, file_path: str = "npc_backgrounds.json"):
        self.npc_data: Dict[str, Any] = {}
        self.load_npc_data(file_path)
    
    def load_npc_data(self, file_path: str) -> None:
        """Load NPC background data from JSON file."""
        try:
            with open(file_path, 'r') as file:
                self.npc_data = json.load(file)
        except FileNotFoundError:
            print(f"Warning: NPC background file {file_path} not found")
            self.npc_data = {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {file_path}")
            self.npc_data = {}
    
    def get_npc_background(self, character_id: str) -> Optional[str]:
        """Get formatted background information for an NPC."""
        if character_id not in self.npc_data:
            return None
        
        npc = self.npc_data[character_id]
        
        background = f"""
Name: {npc['name']}
Role: {npc['role']} ({npc['faction']})

Background: {npc['background']}

Personality: {', '.join(npc['personality_traits'])}

Key Relationships:
{self._format_relationships(npc['key_relationships'])}

Known For: {npc['secret_knowledge']}
Default Disposition: {npc['default_disposition']}

Primary Location: {npc['location_preferences']['primary']}
"""
        return background.strip()
    
    def _format_relationships(self, relationships: Dict[str, str]) -> str:
        """Format relationship data for display."""
        return '\n'.join(f"- {k.title()}: {v}" for k, v in relationships.items())
    
    def get_npc_wares(self, character_id: str) -> list:
        """Get available wares for an NPC."""
        if character_id in self.npc_data:
            return self.npc_data[character_id].get('available_wares', [])
        return []
    
    def get_npc_disposition(self, character_id: str) -> str:
        """Get default disposition for an NPC."""
        if character_id in self.npc_data:
            return self.npc_data[character_id].get('default_disposition', 'neutral')
        return 'neutral' 