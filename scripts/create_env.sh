RESOURCE_GROUP="$1"

echo "Creating .env file for $RESOURCE_GROUP"

OPENAI_API_BASE=$(az deployment group show -g $RESOURCE_GROUP -n openai --query properties.outputs.endpoint.value)
OPENAI_API_KEY=$(az deployment group show -g $RESOURCE_GROUP -n openai --query properties.outputs.key.value)
OPENAI_API_VERSION=2023-06-01-preview

OPENAI_DEPLOYMENT_EMBEDDING=embedding
OPENAI_DEPLOYMENT_COMPLETION=turbo16k

AZURE_SEARCH_ENDPOINT=$(az deployment group show -g $RESOURCE_GROUP -n search-service --query properties.outputs.endpoint.value)
AZURE_SEARCH_KEY=$(az deployment group show -g $RESOURCE_GROUP -n search-service --query properties.outputs.adminKey.value)
AZURE_SEARCH_INDEX=luminis-workshop-demo

cat <<EOT > .env
OPENAI_API_BASE=$OPENAI_API_BASE
OPENAI_API_KEY=$OPENAI_API_KEY
OPENAI_API_VERSION=$OPENAI_API_VERSION

OPENAI_DEPLOYMENT_EMBEDDING=$OPENAI_DEPLOYMENT_EMBEDDING
OPENAI_DEPLOYMENT_COMPLETION=$OPENAI_DEPLOYMENT_COMPLETION

AZURE_SEARCH_ENDPOINT=$AZURE_SEARCH_ENDPOINT
AZURE_SEARCH_KEY=$AZURE_SEARCH_KEY
AZURE_SEARCH_INDEX=$AZURE_SEARCH_INDEX
EOT