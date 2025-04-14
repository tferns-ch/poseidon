# Notification Docker Orchestrator

Docker Compose setup that orchestrates the entire notification system.

```mermaid
flowchart LR
    ExternalApp["External CHS App"] -->|REST| Module1
    Module1["sender-api"] -->|Messages| Kafka
    Kafka["Kafka"] -->|Consume| Module2
    Module2["kafka-consumer"] -->|REST| Module3
    Module3["govuk-notify-api"] -->|REST| GovUKNotify
    Module3 -->|Store| MongoDB
    GovUKNotify["GovUK Notify"]
    MongoDB["MongoDB"]
    
    subgraph OrchestratorSystem["🔱 Notification System Orchestrator"]
        Module1
        Module2
        Module3
        Kafka
        MongoDB
    end
    
    classDef normal fill:#f8f8f8,stroke:#666666,stroke-width:1px,color:#333333,rx:4,ry:4
    classDef external fill:#e6e6e6,stroke:#999999,stroke-width:1px,color:#333333,rx:4,ry:4
    classDef system fill:transparent,stroke:#0077b6,stroke-width:1.5px,stroke-dasharray:3 3,color:#00a8e8,rx:10,ry:10
    
    class Module1,Module2,Module3,Kafka,MongoDB normal;
    class ExternalApp,GovUKNotify external;
    class OrchestratorSystem system;
    
    %% Adding clickable links to GitHub repos
    click Module1 "https://github.com/companieshouse/chs-notification-sender-api" _blank
    click Module2 "https://github.com/companieshouse/chs-notification-kafka-consumer" _blank
    click Module3 "https://github.com/companieshouse/chs-gov-uk-notify-integration-api" _blank
```

## Quick Start

1. Copy `.env.example` to `.env` and update with your repository paths
2. Run `./build.sh` to build all services
3. Run `docker-compose up -d` to start everything

## Services

- Kafka (9092)
- MongoDB (27017)
- Notification Sender API (8081)
- Notification Kafka Consumer (8082)
- GOV.UK Notify Integration API (8083)

Stop with `docker-compose down`
