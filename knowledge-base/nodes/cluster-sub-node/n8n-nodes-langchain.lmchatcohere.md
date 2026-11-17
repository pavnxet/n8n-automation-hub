<!-- n8n built-in node reference: n8n-nodes-langchain.lmchatcohere | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatcohere -->

Use the Cohere Chat Model node to access Cohere's large language models for conversational AI and text generation tasks.

On this page, you'll find the node parameters for the Cohere Chat Model node, and links to more resources.

> **Credentials:**
> Refer to the [Cohere credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/cohere) for authentication information for this node.

## Node parameters

* **Model**: Select the model which will generate the completion. n8n dynamically loads available models from the Cohere API. Learn more in the [Cohere model documentation](https://docs.cohere.com/v2/docs/models#command).

## Node options

* **Sampling Temperature**: Use this option to control the randomness of the sampling process. A higher temperature creates more diverse sampling, but increases the risk of hallucinations.
* **Max Retries**: Enter the maximum number of times to retry a request.

## Templates and examples

[Browse Cohere Chat Model node documentation integration templates](https://n8n.io/integrations/cohere-chat-model) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [Cohere's API documentation](https://docs.cohere.com/v2/reference/about) for more information about the service.
