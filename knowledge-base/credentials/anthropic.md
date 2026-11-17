<!-- n8n built-in node reference: anthropic | source: https://docs.n8n.io/integrations/builtin/credentials/anthropic -->

> **Note:** On n8n Cloud, you can skip setting up Anthropic credentials by selecting **Use Gateway credits** in the credential field of nodes that support it. Refer to [Gateway credits](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/use-n8n-cloud/gateway-credits) for details.

You can use these credentials to authenticate the following nodes:

- [Anthropic](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.anthropic)
- [Anthropic Chat Model](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatanthropic)

## Supported authentication methods

- API key

## Related resources

Refer to [Anthropic's documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api) for more information about the service.

## Using API key

To configure this credential, you'll need an [Anthropic Console account](https://console.anthropic.com) with access to Claude.

Then:

1. In the Anthropic Console, open **Settings >** [**API Keys**](https://console.anthropic.com/settings/keys).
2. Select **+ Create Key**.
3. Give your key a **Name**, like `n8n-integration`.
4. Select **Copy Key** to copy the key.
5. Enter this as the **API Key** in your n8n credential.
6. (Optional) To add custom headers to your API requests:
    1. Enable the **Add Custom Header** toggle.
    2. Enter the **Header Name** for your custom header.
    3. Enter the **Header Value** for your custom header.

Refer to Anthropic's [Intro to Claude](https://docs.anthropic.com/en/docs/intro-to-claude) and [Quickstart](https://docs.anthropic.com/en/docs/quickstart) for more information.
