targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

param appServicePlanName string = ''
param backendServiceName string = ''
param appWhitelistIp string = ''

param searchServiceName string = ''
param searchServiceResourceGroupLocation string = location
param searchServiceSkuName string = 'basic'
param searchIndexName string = 'luminis-workshop-demo'

param openAiResourceName string = ''
param openAiResourceGroupLocation string = location
param openAiSkuName string = ''
param openAIApiVersion string = '2023-06-01-preview'
param completionDeploymentName string = 'turbo16k'
param openAIModelName string = 'gpt-35-turbo-16k'
param embeddingDeploymentName string = 'embedding'
param embeddingModelName string = 'text-embedding-ada-002'

// Used for the Azure AD application
param authClientId string = ''
@secure()
param authClientSecret string = ''

@description('Id of the user or app to assign application roles')
param principalId string = ''

var abbrs = loadJsonContent('abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }


// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'
      capacity: 1
    }
    kind: 'linux'
  }
}

// The application frontend
var appServiceName = !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesAppService}backend-${resourceToken}'
var authIssuerUri = '${environment().authentication.loginEndpoint}${tenant().tenantId}/v2.0'
module backend 'core/host/appservice.bicep' = {
  name: 'web'
  params: {
    name: appServiceName
    location: location
    tags: union(tags, { 'azd-service-name': 'backend' })
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.10'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    appWhitelistIp: appWhitelistIp
    authClientSecret: authClientSecret
    authClientId: authClientId
    authIssuerUri: authIssuerUri
    appSettings: {
      OPENAI_API_BASE: openAi.outputs.endpoint
      OPENAI_API_KEY: openAi.outputs.key
      OPENAI_API_VERSION: openAIApiVersion
      OPENAI_DEPLOYMENT_EMBEDDING: embeddingDeploymentName
      OPENAI_DEPLOYMENT_COMPLETION: completionDeploymentName

      AZURE_SEARCH_ENDPOINT: 'https://${searchService.outputs.name}.search.windows.net'
      AZURE_SEARCH_KEY: searchService.outputs.adminKey
      AZURE_SEARCH_INDEX: searchIndexName
    }
  }
}


module openAi 'core/ai/cognitiveservices.bicep' = {
  name: 'openai'
  params: {
    name: !empty(openAiResourceName) ? openAiResourceName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: openAiResourceGroupLocation
    tags: tags
    sku: {
      name: !empty(openAiSkuName) ? openAiSkuName : 'S0'
    }
    deployments: [
      {
        name: completionDeploymentName
        model: {
          format: 'OpenAI'
          name: openAIModelName
          version: '0613'
        }
        capacity: 10
      }
      {
        name: embeddingDeploymentName
        model: {
          format: 'OpenAI'
          name: embeddingModelName
          version: '2'
        }
        capacity: 10
      }
    ]
  }
}

module searchService 'core/search/search-services.bicep' = {
  name: 'search-service'
  params: {
    name: !empty(searchServiceName) ? searchServiceName : 'gptkb-${resourceToken}'
    location: searchServiceResourceGroupLocation
    tags: tags
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    sku: {
      name: searchServiceSkuName
    }
    semanticSearch: 'disabled'
  }
}


// USER ROLES
module openAiRoleUser 'core/security/role.bicep' = {
  name: 'openai-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User
    principalType: 'User'
  }
}

module searchRoleUser 'core/security/role.bicep' = {
  name: 'search-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f' // Search Index Data Reader
    principalType: 'User'
  }
}

module searchIndexDataContribRoleUser 'core/security/role.bicep' = {
  name: 'search-index-data-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7' // Search Index Data Contributor
    principalType: 'User'
  }
}

module searchServiceContribRoleUser 'core/security/role.bicep' = {
  name: 'search-service-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0' // Search Service Contributor
    principalType: 'User'
  }
}

// SYSTEM IDENTITIES
module openAiRoleBackend 'core/security/role.bicep' = {
  name: 'openai-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User
    principalType: 'ServicePrincipal'
  }
}

module searchRoleBackend 'core/security/role.bicep' = {
  name: 'search-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f' // Search Index Data Reader
    principalType: 'ServicePrincipal'
  }
}


output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId

output BACKEND_URI string = backend.outputs.uri

// openai
output OPENAI_API_BASE string = openAi.outputs.endpoint
output OPENAI_API_KEY string = openAi.outputs.key
output OPENAI_API_VERSION string = openAIApiVersion
output OPENAI_DEPLOYMENT_EMBEDDING string = embeddingDeploymentName
output OPENAI_DEPLOYMENT_COMPLETION string = completionDeploymentName

// search
output AZURE_SEARCH_ENDPOINT string = 'https://${searchService.outputs.name}.search.windows.net'
output AZURE_SEARCH_KEY string = openAi.outputs.key
output AZURE_SEARCH_INDEX string = searchIndexName

output AUTH_ISSUER_URI string = authIssuerUri


output BACKEND_RESOURCE_NAME string = appServiceName
