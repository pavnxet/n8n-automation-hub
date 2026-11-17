<!-- n8n built-in node reference: moonshot | source: https://docs.n8n.io/integrations/builtin/credentials/moonshot -->

> **Note:** On n8n Cloud, you can skip setting up Moonshot credentials by selecting **Use Gateway credits** in the credential field of nodes that support it. Refer to [Gateway credits](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/use-n8n-cloud/gateway-credits) for details.

You can use these credentials to authenticate the following nodes:

* [Moonshot Kimi](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.moonshot)
* [Moonshot Kimi Chat Model](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatmoonshot)

## Prerequisites

Create a [Kimi API Platform account](https://platform.kimi.ai/).

## Supported authentication methods

- API key

## Related resources

Refer to [Moonshot's documentation](https://platform.kimi.ai/docs/) for more information about the service.

## Using API key

To configure this credential, you'll need a [Kimi API Platform](https://platform.kimi.ai/) account and an API key:

1. In the [Kimi API Platform console](https://platform.kimi.ai/console/api-keys), select **API Keys**.
2. Select **Create API Key**.
3. Enter a **name** and **project** for the API key.
4. Copy the API key and enter it in your n8n credential.
