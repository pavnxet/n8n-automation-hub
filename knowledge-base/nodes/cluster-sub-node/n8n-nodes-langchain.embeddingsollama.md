<!-- n8n built-in node reference: n8n-nodes-langchain.embeddingsollama | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.embeddingsollama -->

Use the Embeddings Ollama node to generate embeddings[^1] for a given text.

On this page, you'll find the node parameters for the Embeddings Ollama node, and links to more resources.

> **Credentials:**
> Refer to the [Ollama credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/ollama) for authentication information for this node.

## Node parameters

* **Model**: Select the model to use to generate the embedding. Choose from:
    * [all-minilm](https://ollama.com/library/all-minilm) (384 Dimensions)
    * [nomic-embed-text](https://ollama.com/library/nomic-embed-text) (768 Dimensions)

Learn more about available models in [Ollama's models documentation](https://ollama.ai/library).

## Templates and examples

[Browse Embeddings Ollama node documentation integration templates](https://n8n.io/integrations/embeddings-ollama) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [LangChain's Ollama embeddings documentation](https://docs.langchain.com/oss/javascript/integrations/embeddings/ollama) for more information about the service.

[^1]: Embeddings are numerical representations of data using vectors. They're used by AI to interpret complex data and relationships by mapping values across many dimensions. Vector databases, or vector stores, are databases designed to store and access embeddings.
