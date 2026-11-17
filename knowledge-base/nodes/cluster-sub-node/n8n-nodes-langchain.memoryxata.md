<!-- n8n built-in node reference: n8n-nodes-langchain.memoryxata | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.memoryxata -->

Use the Xata node to use Xata as a memory[^1] server.
On this page, you'll find a list of operations the Xata node supports, and links to more resources.

> **Credentials:**
> Refer to the [Xata credentials documentation](https://docs.n8n.io/integrations/builtin/credentials/xata) for authentication information for this node.

## Node parameters

-   **Session ID**: Enter the ID to use to store the memory in the workflow data.
-   **Context Window Length**: Enter the number of previous interactions to consider for context.

## Templates and examples

[Browse Xata node documentation integration templates](https://n8n.io/integrations/xata) or [search all templates](https://n8n.io/workflows/)

## Related resources

## Single memory instance

If you add more than one Xata node to your workflow, all nodes access the same memory instance by default. Be careful when doing destructive actions that override existing memory contents, such as the override all messages operation in the [Chat Memory Manager](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.memorymanager) node. If you want more than one memory instance in your workflow, set different session IDs in different memory nodes.

[^1]: In an AI context, memory allows AI tools to persist message context across interactions. This allows you to have a continuing conversations with AI agents, for example, without submitting ongoing context with each message. In n8n, AI agent nodes can use memory, but AI chains can't.
