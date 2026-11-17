<!-- n8n built-in node reference: n8n-nodes-base.errortrigger | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.errortrigger -->

You can use the Error Trigger node to create error workflows. When another linked workflow fails, this node gets details about the failed workflow and the errors, and runs the error workflow.

## Usage

Note the following:

* You have to publish the workflow that uses the **Error Trigger** node.
* If a workflow contains the Error Trigger node, by default, the workflow uses itself as the error workflow.
* You can't test error workflows when running workflows manually. The Error Trigger only runs when an automatic workflow errors.

## Templates and examples

[Browse Error Trigger node documentation integration templates](https://n8n.io/integrations/error-trigger) or [search all templates](https://n8n.io/workflows/)

## Related resources

You can use the [Stop And Error](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.stopanderror) node to send custom messages to the Error Trigger.

Read more about [Error workflows](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/flow-logic/handle-errors-gracefully) in n8n workflows. 

## Error data
