<!-- n8n built-in node reference: n8n-nodes-langchain.lmcohere | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmcohere -->

Use the Cohere Model node to use Cohere's models.

On this page, you'll find the node parameters for the Cohere Model node, and links to more resources.

This node lacks tools support, so it won't work with the [AI Agent](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent) node. Instead, connect it with the [Basic LLM Chain](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.chainllm) node.

> **Credentials:**
> Refer to the [Cohere credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/cohere) for authentication information for this node.

## Node Options

* **Maximum Number of Tokens**: Enter the maximum number of tokens used, which sets the completion length.
* **Sampling Temperature**: Use this option to control the randomness of the sampling process. A higher temperature creates more diverse sampling, but increases the risk of hallucinations.

## Templates and examples

[Browse Cohere Model node documentation integration templates](https://n8n.io/integrations/cohere-model) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [LangChain's Cohere documentation](https://docs.langchain.com/oss/javascript/integrations/llms/cohere) for more information about the service.
