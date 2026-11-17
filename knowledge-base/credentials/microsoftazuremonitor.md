<!-- n8n built-in node reference: microsoftazuremonitor | source: https://docs.n8n.io/integrations/builtin/credentials/microsoftazuremonitor -->

> **Credential-only node:** This node exists only to supply credentials to other nodes.

## Prerequisites

* Create a Microsoft Azure account or subscription
* An app registered in Microsoft Entra ID

## Supported authentication methods

* OAuth2

## Related resources

Refer to [Microsoft Azure Monitor's API documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/azure-monitor-rest-api-index) for more information about the service.

## Using OAuth2

To configure this credential, you'll need a Microsoft Azure account and:

- A **Client ID**
- A **Client Secret**
- A **Tenant ID**
- The **Resource** you plan to access

Refer to [Microsoft Azure Monitor's API documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/api/access-api?tabs=rest#set-up-authentication) for more information about authenticating to the service.
