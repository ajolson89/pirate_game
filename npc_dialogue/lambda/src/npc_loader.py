"""
NPC Loader Module
Handles loading and managing NPC data from DynamoDB
"""

import boto3
from typing import Dict, Optional
from aws_lambda_powertools import Logger
import os

logger = Logger()

class NPCLoader:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.environ['NPC_DATA_TABLE'])
    
    def get_npc_background(self, character_id: str) -> Optional[Dict]:
        """
        Retrieve NPC background data from DynamoDB
        
        Args:
            character_id: The unique identifier for the NPC
            
        Returns:
            Dict containing NPC data or None if not found
        """
        try:
            response = self.table.get_item(
                Key={'character_id': character_id}
            )
            
            if 'Item' in response:
                logger.info(f"Retrieved NPC data for {character_id}")
                return response['Item']
            else:
                logger.warning(f"No NPC data found for {character_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving NPC data for {character_id}: {str(e)}")
            return None
    
    def get_npc_knowledge(self, character_id: str) -> Dict:
        """
        Get NPC's knowledge base
        
        Args:
            character_id: The unique identifier for the NPC
            
        Returns:
            Dict containing NPC's knowledge or empty dict if not found
        """
        npc_data = self.get_npc_background(character_id)
        return npc_data.get('knowledge', {}) if npc_data else {}
    
    def get_npc_quests(self, character_id: str) -> Dict:
        """
        Get NPC's available quests
        
        Args:
            character_id: The unique identifier for the NPC
            
        Returns:
            Dict containing NPC's quests or empty dict if not found
        """
        npc_data = self.get_npc_background(character_id)
        return npc_data.get('quests', {}) if npc_data else {}