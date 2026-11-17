<!-- n8n built-in node reference: n8n-nodes-base.stopanderror | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.stopanderror -->

Use the Stop And Error node to display custom error messages, cause executions to fail under certain conditions, and send custom error information to error workflows.

## Operations

* Error Message
* Error Object

## Node parameters

Both operations include one node parameter, the **Error Type**. Use this parameter to select the type of error to throw. Choose between the two operations: **Error Message** and **Error Object**.

The other parameters depend on which operation you select.

### Error Message parameters

The Error Message Error Type adds one parameter, the **Error Message** field. Enter the message you'd like to throw.

### Error Object parameters

The Error Object Error Type adds one parameter, the **Error Object**. Enter a JSON object that contains the error properties you'd like to throw.

## Templates and examples

[Browse Stop And Error integration templates](https://n8n.io/integrations/stop-and-error) or [search all templates](https://n8n.io/workflows/)

## Related resources

You can use the Stop And Error node with the [Error trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.errortrigger) node.

Read more about [Error workflows](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/flow-logic/handle-errors-gracefully) in n8n workflows.
