<!-- n8n built-in node reference: trellixepo | source: https://docs.n8n.io/integrations/builtin/credentials/trellixepo -->

> **Credential-only node:** This node exists only to supply credentials to other nodes.

## Prerequisites

Create a [Trellix ePolicy Orchestrator](https://www.trellix.com/products/epo/) account.

## Supported authentication methods

- Basic auth

## Related resources

Refer to [Trellix ePO's documentation](https://docs.trellix.com/docs/trellix-epolicy-orchestrator-on-prem-web-api-scripting-reference-guide) for more information about the service.

This is a credential-only node. Refer to [Custom API operations](https://docs.n8n.io/integrations/builtin/custom-api-actions-for-existing-nodes) to learn more. View [example workflows and related content](https://n8n.io/integrations/trellix-epo/) on n8n's website.

## Using basic auth

To configure this credential, you'll need:

- A **Username** to connect as.
- A **Password** for that user account.

n8n uses these fields to build the `-u` parameter in the format of `-u username:pw`. Refer to [Web API basics](https://docs.trellix.com/docs/web-api-basics) for more information.
