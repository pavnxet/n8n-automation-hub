<!-- n8n built-in node reference: n8n-nodes-langchain.toolcode | source: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolcode -->

Use the Custom Code Tool node to write code that an agent[^1] can run.

On this page, you'll find the node parameters for the Custom Code Tool node and links to more resources.

## Node parameters

### Description

Give your custom code a description. This tells the agent when to use this tool. For example:

> Call this tool to get a random color. The input should be a string with comma separated names of colors to exclude.

### Language

You can use JavaScript or Python.

### JavaScript / Python box

Write the code here.

You can access the tool input using `query`. For example, to take the input string and lowercase it:

```js
let myString = query;
return myString.toLowerCase();
```

## Templates and examples

[Browse Custom Code Tool node documentation integration templates](https://n8n.io/integrations/code-tool) or [search all templates](https://n8n.io/workflows/)

## Related resources

[^1]: AI agents are artificial intelligence systems capable of responding to requests, making decisions, and performing real-world tasks for users. They use large language models (LLMs) to interpret user input and make decisions about how to best process requests using the information and resources they have available.
