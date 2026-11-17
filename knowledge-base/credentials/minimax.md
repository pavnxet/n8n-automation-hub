<!-- n8n built-in node reference: minimax | source: https://docs.n8n.io/integrations/builtin/credentials/minimax -->

> **Note:** On n8n Cloud, you can skip setting up MiniMax credentials by selecting **Use Gateway credits** in the credential field of nodes that support it. Refer to [Gateway credits](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/use-n8n-cloud/gateway-credits) for details.

You can use these credentials to authenticate the following nodes:

* [MiniMax](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.minimax)
* [MiniMax Chat Model](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatminimax)

## Prerequisites

Create a [MiniMax](https://platform.minimax.io/) account.

## Supported authentication methods

- API key

## Related resources

Refer to [MiniMax's API documentation](https://platform.minimax.io/docs/guides/models-intro) for more information about the service.

## Using API key

To configure this credential, you'll need:

- A **Region**: Select **International** or **China** depending on your MiniMax account.
- An **API Key**

To get your API key:

1. Log in to your [MiniMax account](https://platform.minimax.io/).
2. Go to **Account** > **API Keys**.
3. Select **Create API Key**.
4. Copy the key and enter it in your n8n credential.
