<!-- n8n built-in node reference: thehive | source: https://docs.n8n.io/integrations/builtin/credentials/thehive -->

You can use these credentials to authenticate the following nodes:

- [TheHive](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.thehive)

> **TheHive and TheHive 5:**
> n8n provides two nodes for TheHive. Use these credentials with TheHive node for TheHive 3 or TheHive 4. If you're using TheHive5 node, use [TheHive 5 credentials](https://docs.n8n.io/integrations/builtin/credentials/thehive5).

## Prerequisites

Install [TheHive](https://docs.strangebee.com/thehive/installation/installation-methods/) on your server.

## Supported authentication methods

- API key

## Related resources

Refer to the [TheHive 5 API documentation](https://docs.strangebee.com/thehive/api-docs/) and [TheHive's documentation](https://docs.strangebee.com/) for more information about the services. The API docs for TheHive 3 and 4 are no longer online.

## Using API key

To configure this credential, you'll need:

- An **API Key**: Create an API key from **Organization > Create API Key**. Refer to the [TheHive 5 API documentation](https://docs.strangebee.com/thehive/api-docs/) for more information.
- Your **URL**: The URL of your TheHive server.
- An **API Version**: Choose between:
    - **TheHive 3 (api v0)**
    - **TheHive 4 (api v1)**
    - For TheHive 5, use [TheHive 5 credentials](https://docs.n8n.io/integrations/builtin/credentials/thehive5) instead.
- **Ignore SSL Issues**: When turned on, n8n will connect even if SSL certificate validation fails.
