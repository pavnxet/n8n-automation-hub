<!-- n8n built-in node reference: n8n-nodes-langchain.embeddingshuggingfaceinference | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.embeddingshuggingfaceinference -->

Use the Embeddings HuggingFace Inference node to generate embeddings[^1] for a given text.

On this page, you'll find the node parameters for the Embeddings HuggingFace Inference, and links to more resources.

> **Credentials:**
> Refer to the [Hugging Face credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/huggingface) for authentication information for this node.

## Node parameters

* **Model**: Select the model to use to generate the embedding.

Refer to the [Hugging Face models documentation](https://huggingface.co/models?other=embeddings) for available models.

## Node options

* **Custom Inference Endpoint**: Enter the URL of your deployed model, hosted by HuggingFace. If you set this, n8n ignores the **Model Name**.

Refer to [HuggingFace's guide to inference](https://huggingface.co/inference-endpoints) for more information.

## Templates and examples

[Browse Embeddings HuggingFace Inference node documentation integration templates](https://n8n.io/integrations/embeddings-hugging-face-inference) or [search all templates](https://n8n.io/workflows/)

## Related resources

[^1]: Embeddings are numerical representations of data using vectors. They're used by AI to interpret complex data and relationships by mapping values across many dimensions. Vector databases, or vector stores, are databases designed to store and access embeddings.
