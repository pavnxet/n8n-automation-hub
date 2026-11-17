<!-- n8n built-in node reference: n8n-nodes-base.if | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if -->

Use the If node to split a workflow conditionally based on comparison operations.

## Add conditions

Create comparison **Conditions** for your If node.

- Use the data type dropdown to select the data type and comparison operation type for your condition. For example, to filter for dates after a particular date, select **Date & Time > is after**.
- The fields and values to enter into the condition change based on the data type and comparison you select. Refer to [Available data type comparisons](#available-data-type-comparisons) for a full list of all comparisons by data type.

Select **Add condition** to create more conditions.

### Combining conditions

You can choose to keep data:

* When it meets all conditions: Create two or more conditions and select **AND** in the dropdown between them.
* When it meets any of the conditions: Create two or more conditions and select **OR** in the dropdown between them.

## Templates and examples

[Browse If integration templates](https://n8n.io/integrations/if) or [search all templates](https://n8n.io/workflows/)

## Branch execution with If and Merge nodes

## Related resources

Refer to [Splitting with conditionals](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/flow-logic/split-with-conditionals) for more information on using conditionals to create complex logic in n8n.

If you need more than two conditional outputs, use the [Switch node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.switch).
