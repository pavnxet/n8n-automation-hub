<!-- n8n built-in node reference: ollama | source: https://docs.n8n.io/integrations/builtin/credentials/ollama -->

You can use these credentials to authenticate the following nodes:

* [Ollama](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmollama)
* [Chat Ollama](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatollama)
* [Embeddings Ollama](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.embeddingsollama)

## Prerequisites

Create and run an [Ollama](https://ollama.com/) instance with one user. Refer to the Ollama [Quick Start](https://github.com/ollama/ollama/blob/main/README.md#quickstart) for more information.

## Supported authentication methods

* Instance URL

## Related resources

Refer to [Ollama's API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md) for more information about the service.

## Using instance URL

To configure this credential, you'll need:

* The **Base URL** of your Ollama instance or remote authenticated Ollama instances.
* (Optional) The **API Key** for Bearer token authentication if connecting to a remote, authenticated proxy.

The default **Base URL** is `http://localhost:11434`, but if you've set the `OLLAMA_HOST` environment variable, enter that value. If you have issues connecting to a local n8n server, try `127.0.0.1` instead of `localhost`.

If you're connecting to Ollama through authenticated proxy services (such as [Open WebUI](https://docs.openwebui.com/getting-started/api-endpoints/#-ollama-api-proxy-support)) you must include an API key. If you don't need authentication, leave this field empty. When provided, the API key is sent as a Bearer token in the `Authorization` header of the request to the Ollama API.

Refer to [How do I configure Ollama server?](https://github.com/ollama/ollama/blob/main/docs/faq.mdx#how-do-i-configure-ollama-server) for more information.

### Ollama and self-hosted n8n

If Ollama and n8n run in separate Docker containers, connect both containers to the same user-defined bridge network. Set **Base URL** to `http://:11434`. Replace `` with your Ollama container's name. For example, for a container with the name `ollama`, use `http://ollama:11434`.

For the setup steps, refer to [Ollama Chat Model node common issues](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatollama/common-issues#if-ollama-and-n8n-are-running-in-separate-docker-containers).
