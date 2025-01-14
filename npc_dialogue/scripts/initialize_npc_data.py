"""
NPC Data Initialization Script
Populates DynamoDB with NPC character backgrounds and initial data from custom format
"""

import boto3
import json
from typing import Dict, List
from datetime import datetime
import argparse

def load_npc_backgrounds() -> Dict:
    """
    Load NPC background data from JSON file
    """
    try:
        with open('data/npc_backgrounds.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: npc_backgrounds.json not found in data directory")
        raise
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in npc_backgrounds.json")
        raise

def initialize_npc_table(table_name: str, profile_name: str = 'default', region: str = 'us-east-1'):
    """
    Initialize DynamoDB table with NPC data
    """
    # Create session with specific profile
    session = boto3.Session(profile_name=profile_name, region_name=region)
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    # Load NPC background data
    npc_data = load_npc_backgrounds()
    
    # Insert each NPC's data into DynamoDB
    for character_id, data in npc_data.items():
        try:
            # Create the base item with required fields
            item = {
                'character_id': character_id,
                'name': data.get('name', character_id),
                'background': data.get('background', ''),
                'occupation': data.get('occupation', ''),
                'location': data.get('location', ''),
                'knowledge': data.get('knowledge', {}),
                'quests': data.get('quests', {}),
                'dialogue_style': data.get('dialogue_style', {}),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Add optional fields if they exist
            if 'personality' in data:
                item['personality'] = data['personality']
            
            if 'relationships' in data:
                item['relationships'] = data['relationships']
                
            if 'quest_flags' in data:
                item['quest_flags'] = data['quest_flags']
                
            if 'inventory' in data:
                item['inventory'] = data['inventory']

            # Store in DynamoDB
            table.put_item(Item=item)
            print(f"Successfully initialized {character_id}")
            
        except Exception as e:
            print(f"Error initializing {character_id}: {str(e)}")

def verify_npc_data(table_name: str, profile_name: str = 'default', region: str = 'us-east-1'):
    """
    Verify that all NPCs were properly initialized
    """
    session = boto3.Session(profile_name=profile_name, region_name=region)
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    try:
        response = table.scan()
        items = response.get('Items', [])
        print(f"\nVerification: Found {len(items)} NPCs in database")
        for item in items:
            print(f"- {item['character_id']}: {item.get('name', 'No name provided')}")
    except Exception as e:
        print(f"Error verifying NPC data: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize NPC data in DynamoDB')
    parser.add_argument('table_name', help='Name of the DynamoDB table')
    parser.add_argument('--profile', default='personal', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region name')
    
    args = parser.parse_args()
    
    print(f"Initializing NPC data in table: {args.table_name}")
    print(f"Using AWS profile: {args.profile}")
    print(f"Using AWS region: {args.region}")
    initialize_npc_table(args.table_name, args.profile, args.region)
    verify_npc_data(args.table_name, args.profile, args.region) 