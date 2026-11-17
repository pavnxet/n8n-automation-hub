<!-- n8n built-in node reference: n8n-nodes-langchain.documentgithubloader | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.documentgithubloader -->

> **Feature availability:**
> The GitHub Document Loader node is deprecated from n8n 1.122.0. Refer to [Deprecated and versioned nodes](https://docs.n8n.io/integrations/builtin/deprecated-nodes) for more information.

Use the GitHub Document Loader node to load data from a GitHub repository for [vector stores](#user-content-fn-1)[^1] or summarization.

On this page, you'll find the node parameters for the GitHub Document Loader node, and links to more resources.

> **Credentials:**
> Refer to the [GitHub credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/github) for authentication information for this node. This node doesn't support OAuth for authentication.

## Node parameters

* **Text Splitting**: Choose from:
	* **Simple**: Uses the [Recursive Character Text Splitter](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.textsplitterrecursivecharactertextsplitter) with a chunk size of 1000 and an overlap of 200.
    * **Custom**: Allows you to connect a text splitter of your choice.
* **Repository Link**: Enter the URL of your GitHub repository.
* **Branch**: Enter the branch name to use.

## Node options

* **Recursive**: Select whether to include sub-folders and files (turned on) or not (turned off).
* **Ignore Paths**: Enter directories to ignore.

## Templates and examples

[Browse GitHub Document Loader node documentation integration templates](https://n8n.io/integrations/github-document-loader) or [search all templates](https://n8n.io/workflows/)

## Related resources

[^1]: A vector store, or vector database, stores mathematical representations of information. Use with embeddings and retrievers to create a database that your AI can access when answering questions.
