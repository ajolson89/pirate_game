#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { NPCDialogueStack } from '../lib/npc_dialogue_stack';

const app = new cdk.App();
new NPCDialogueStack(app, 'NPCDialogueStack', {
  env: { 
    account: process.env.CDK_DEFAULT_ACCOUNT, 
    region: process.env.CDK_DEFAULT_REGION,
  },
  description: 'NPC Dialogue System using AWS Bedrock',
});