<!-- n8n built-in node reference: n8n-nodes-langchain.embeddingscohere | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.embeddingscohere -->

Use the Embeddings Cohere node to generate embeddings[^1] for a given text.

On this page, you'll find the node parameters for the Embeddings Cohere node, and links to more resources.

> **Credentials:**
> Refer to the [Cohere credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/cohere) for authentication information for this node.

## Node parameters

* **Model**: Select the model to use to generate the embedding. Choose from:
    * **Embed-English-v2.0(4096 Dimensions)**
	* **Embed-English-Light-v2.0(1024 Dimensions)**
	* **Embed-Multilingual-v2.0(768 Dimensions)**

Learn more about available models in [Cohere's models documentation](https://docs.cohere.com/docs/models).

## Templates and examples

[Browse Embeddings Cohere node documentation integration templates](https://n8n.io/integrations/embeddings-cohere) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [LangChain's Cohere embeddings documentation](https://docs.langchain.com/oss/javascript/integrations/embeddings/cohere) for more information about the service.

[^1]: Embeddings are numerical representations of data using vectors. They're used by AI to interpret complex data and relationships by mapping values across many dimensions. Vector databases, or vector stores, are databases designed to store and access embeddings.
