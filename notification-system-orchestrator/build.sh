#!/bin/bash

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "Error: .env file not found"
  exit 1
fi

SERVICE_NAMES=("notification-sender-api" "notification-kafka-consumer" "gov-uk-notify-integration-api")
SERVICE_PATHS=("$SENDER_REPO_PATH" "$CONSUMER_REPO_PATH" "$NOTIFY_REPO_PATH")

for i in "${!SERVICE_NAMES[@]}"; do
  service_name="${SERVICE_NAMES[$i]}"
  repo_path="${SERVICE_PATHS[$i]}"
  
  echo "Building $service_name..."
  
  if [ ! -d "$repo_path" ]; then
    echo "Error: Repository path for $service_name is not valid: $repo_path"
    exit 1
  fi
  
  cd "$repo_path"
  if ! mvn clean package -DskipTests; then
    echo "Error building $service_name"
    exit 1
  fi
  
  echo "$service_name built successfully"
done

echo "All services built successfully"
echo "You can now run 'docker-compose up -d' to start the services"
