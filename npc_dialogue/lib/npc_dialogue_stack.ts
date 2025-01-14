/**
 * NPC Dialogue System - AWS Infrastructure Stack
 * 
 * This stack creates all necessary AWS resources for the NPC dialogue system:
 * - DynamoDB tables for chat history and NPC data
 * - Lambda function for dialogue generation
 * - API Gateway for HTTP endpoints
 * - IAM roles and permissions
 * - CloudWatch logging
 * 
 * @package NPCDialogue
 */

import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export class NPCDialogueStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB Tables
    // Chat History Table: Stores all NPC-player interactions
    // Uses composite key of game_id#character_id for multi-game support
    const chatHistoryTable = new dynamodb.Table(this, 'ChatHistoryTable', {
      partitionKey: { name: 'composite_key', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development only
    });
    
    // Global Secondary Index for querying conversations by game_id
    // Enables retrieval of all NPC interactions within a specific game
    chatHistoryTable.addGlobalSecondaryIndex({
      indexName: 'GameIdIndex',
      partitionKey: { name: 'game_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING }
    });
    
    // NPC Data Table: Stores static NPC information and backgrounds
    const npcDataTable = new dynamodb.Table(this, 'NPCData', {
      partitionKey: { name: 'character_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      // Add optional secondary indexes if needed
      timeToLiveAttribute: 'ttl',  // If you want to expire old versions
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,  // If you want to track changes
    });

    // Add GSI for location-based queries if needed
    // npcDataTable.addGlobalSecondaryIndex({
    //   indexName: 'LocationIndex',
    //   partitionKey: { name: 'location', type: dynamodb.AttributeType.STRING },
    //   projectionType: dynamodb.ProjectionType.ALL
    // });

    // // Add GSI for occupation-based queries if needed
    // npcDataTable.addGlobalSecondaryIndex({
    //   indexName: 'OccupationIndex',
    //   partitionKey: { name: 'occupation', type: dynamodb.AttributeType.STRING },
    //   projectionType: dynamodb.ProjectionType.ALL
    // });

    // Lambda Layer: Contains all Python dependencies
    const lambdaLayer = new lambda.LayerVersion(this, 'NPCDialogueDependencies', {
      code: lambda.Code.fromAsset('lambda_layer.zip'),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_9],
      description: 'Dependencies for NPC Dialogue Lambda function',
    });
    
    const dialogueFunction = new lambda.Function(this, 'NPCDialogueFunction', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'src.main.lambda_handler',
      code: lambda.Code.fromAsset('lambda'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      layers: [lambdaLayer],
      environment: {
        POWERTOOLS_SERVICE_NAME: 'NPCDialogue',
        LOG_LEVEL: 'DEBUG',
        CHAT_HISTORY_TABLE: chatHistoryTable.tableName,
        NPC_DATA_TABLE: npcDataTable.tableName,
      },
    });

    // IAM Permissions Setup
    // Grant DynamoDB access
    chatHistoryTable.grantReadWriteData(dialogueFunction);  // Full access to chat history
    npcDataTable.grantReadData(dialogueFunction);  // Read-only for NPC data
    
    // Grant Amazon Bedrock permissions for LLM access
    dialogueFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:ListFoundationModels',
      ],
      resources: ['*'],  // TODO: Restrict to specific model ARNs in production
    }));

    // Setup CloudWatch logging permissions
    dialogueFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents',
      ],
      resources: ['*'],
    }));

    // API Gateway Configuration
    // Creates REST API with CORS support
    const api = new apigateway.RestApi(this, 'NPCDialogueApi', {
      restApiName: 'NPC Dialogue Service',
      description: 'API for generating NPC dialogue using AWS Bedrock',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
      },
    });

    // API Endpoints Setup
    const dialogueIntegration = new apigateway.LambdaIntegration(dialogueFunction);

    // POST /generate-dialogue - Main dialogue generation endpoint
    const dialogueResource = api.root.addResource('generate-dialogue');
    dialogueResource.addMethod('POST', dialogueIntegration, {
      apiKeyRequired: true,
    });

    // GET /chat-history/{character_id} - Retrieve conversation history
    const historyResource = api.root.addResource('chat-history')
      .addResource('{character_id}');
    historyResource.addMethod('GET', dialogueIntegration, {
      apiKeyRequired: true,
    });

    // API Security Configuration
    // Setup API key and usage plan for rate limiting
    const apiKey = api.addApiKey('NPCDialogueApiKey');
    const usagePlan = api.addUsagePlan('NPCDialogueUsagePlan', {
      name: 'Standard',
      throttle: {
        rateLimit: 10,   // Requests per second
        burstLimit: 20,  // Maximum burst size
      },
      quota: {
        limit: 1000,     // Requests per day
        period: apigateway.Period.DAY,
      },
    });

    // Associate API key with usage plan
    usagePlan.addApiKey(apiKey);
    usagePlan.addApiStage({
      stage: api.deploymentStage,
    });

    // Stack Outputs
    // Expose important resource information
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'API Gateway URL',
    });

    new cdk.CfnOutput(this, 'ApiKeyId', {
      value: apiKey.keyId,
      description: 'API Key ID',
    });

    new cdk.CfnOutput(this, 'ChatHistoryTableName', {
      value: chatHistoryTable.tableName,
      description: 'DynamoDB Chat History Table Name',
    });

    new cdk.CfnOutput(this, 'NPCDataTableName', {
      value: npcDataTable.tableName,
      description: 'DynamoDB NPC Data Table Name',
    });
  }
} 