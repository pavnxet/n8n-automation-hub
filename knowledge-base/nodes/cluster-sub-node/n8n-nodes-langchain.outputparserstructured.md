<!-- n8n built-in node reference: n8n-nodes-langchain.outputparserstructured | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.outputparserstructured -->

Use the Structured Output Parser node to return fields based on a JSON Schema.

On this page, you'll find the node parameters for the Structured Output Parser node, and links to more resources.

## Node parameters

* **Schema Type**: Define the output structure and validation. You have two options to provide the schema:

## Templates and examples

[Browse n8n-nodes-langchain.outputparserstructured integration templates](https://n8n.io/integrations/structured-output-parser) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [LangChain's structured output documentation](https://docs.langchain.com/oss/javascript/langchain/structured-output) for more information about the service.

## Common issues

For common questions or issues and suggested solutions, refer to [Common issues](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.outputparserstructured/common-issues).

---

## Structured Output Parser node common issues

## Common issues

Here are some common errors and issues with the [Structured Output Parser node](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.outputparserstructured) and steps to resolve or troubleshoot them.

### Processing parameters

The Structured Output Parser node is a sub-node[^1]. Sub-nodes behave differently than other nodes when processing multiple items using expressions.

Most nodes, including [root nodes](#user-content-fn-2)[^2], take any number of items as input, process these items, and output the results. You can use expressions to refer to input items, and the node resolves the expression for each item in turn. For example, given an input of five name values, the expression `{{ $json.name }}` resolves to each name in turn.

In sub-nodes, the expression always resolves to the first item. For example, given an input of five name values, the expression `{{ $json.name }}` always resolves to the first name.

### Adding the structured output parser node to AI nodes

You can attach output parser nodes to select [AI root nodes](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes).

To add the Structured Output Parser to a node, enable the **Require Specific Output Format** option in the AI root node you wish to format. Once the option is enabled, a new **output parser** attachment point is displayed. Click the **output parser** attachment point to add the Structured Output Parser node to the node.

### Using the structured output parser to format intermediary steps

The Structured Output Parser node structures the final output from AI agents. It's not intended to structure intermediary output to pass to other AI tools or stages.

To request a specific format for intermediary output, include the response structure in the **System Message** for the **AI Agent**. The message can include either a schema or example response for the agent to use as a template for its results.

### Structuring output from agents

Structured output parsing is often not reliable when working with [agents](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent).

If your workflow uses agents, n8n recommends using a separate [LLM-chain](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.chainllm) to receive the data from the agent and parse it. This leads to better, more consistent results than parsing directly in the agent workflow.

[^1]: n8n cluster nodes consist of one or more sub-nodes connected to a root node. Sub-nodes extend the functionality of the root node, providing access to specific services or resources or offering specific types of dedicated processing, like calculator functionality, for example.
[^2]: Each n8n cluster node contains a single root node that defines the main functionality of the cluster. One or more sub-nodes attach to the root node to extend its functionality.
