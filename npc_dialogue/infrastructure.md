graph TD
    subgraph "AWS Cloud"
        API[API Gateway] --> Lambda[Lambda Function]
        Lambda --> Bedrock[Amazon Bedrock]
        Lambda --> DDB1[DynamoDB<br/>Chat History Table]
        Lambda --> DDB2[DynamoDB<br/>NPC Data Table]
        
        subgraph "DynamoDB Tables"
            DDB1
            DDB2
        end
        
        subgraph "Lambda Resources"
            Lambda --> CW[CloudWatch Logs]
            Lambda --> XRay[X-Ray Tracing]
        end
        
        subgraph "Security"
            API --> ApiKey[API Key]
            Lambda --> IAM[IAM Role]
            IAM --> Perms[Permissions:<br/>Bedrock<br/>DynamoDB<br/>CloudWatch]
        end
    end
    
    Client[Client Application] --> API
    Client --> ApiKey
    
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef client fill:#85B09A,stroke:#232F3E,stroke-width:2px,color:white;
    
    class API,Lambda,Bedrock,DDB1,DDB2,CW,XRay,IAM aws;
    class Client client;