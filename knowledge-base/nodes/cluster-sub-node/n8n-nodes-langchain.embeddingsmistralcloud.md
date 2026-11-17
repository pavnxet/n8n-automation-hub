<!-- n8n built-in node reference: n8n-nodes-langchain.embeddingsmistralcloud | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.embeddingsmistralcloud -->

Use the Embeddings Mistral Cloud node to generate embeddings[^1] for a given text.

On this page, you'll find the node parameters for the Embeddings Mistral Cloud node, and links to more resources.

> **Credentials:**
> Refer to the [Mistral Cloud credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/mistral) for authentication information for this node.

## Node parameters

* **Model**: Select the model to use to generate the embedding.

Learn more about available models in [Mistral's models documentation](https://docs.mistral.ai/models/).

## Node options

* **Batch Size**: Enter the maximum number of documents to send in each request.
* **Strip New Lines**: Select whether to remove new line characters from input text (turned on) or not (turned off). n8n enables this by default.

## Templates and examples

[Browse Embeddings Mistral Cloud node documentation integration templates](https://n8n.io/integrations/embeddings-mistral-cloud) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [LangChain's Mistral embeddings documentation](https://docs.langchain.com/oss/javascript/integrations/embeddings/mistralai) for more information about the service.

[^1]: Embeddings are numerical representations of data using vectors. They're used by AI to interpret complex data and relationships by mapping values across many dimensions. Vector databases, or vector stores, are databases designed to store and access embeddings.
