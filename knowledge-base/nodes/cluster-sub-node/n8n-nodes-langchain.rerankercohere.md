<!-- n8n built-in node reference: n8n-nodes-langchain.rerankercohere | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.rerankercohere -->

The Reranker Cohere node allows you to rerank[^1] the resulting chunks from a [vector store](#user-content-fn-2)[^2]. You can connect this node to a vector store.

The reranker reorders the list of documents retrieved from a vector store for a given query in order of descending relevance.

On this page, you'll find the node parameters for the Reranker Cohere node, and links to more resources.

> **Credentials:**
> Refer to the [Cohere credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/cohere) for authentication information for this node.

## Node parameters

### Model

Choose the reranking model to use. You can find out more about the available models in [Cohere's model documentation](https://docs.cohere.com/docs/models#rerank).

## Templates and examples

[Browse Reranker Cohere integration templates](https://n8n.io/integrations/reranker-cohere) or [search all templates](https://n8n.io/workflows/)

## Related resources

[^1]: Reranking is a technique that refines the order of a list of candidate documents to improve the relevance of search results. Retrieval-Augmented Generation (RAG) and other applications use reranking to prioritize the most relevant information for generation or downstream tasks.
[^2]: A vector store, or vector database, stores mathematical representations of information. Use with embeddings and retrievers to create a database that your AI can access when answering questions.
