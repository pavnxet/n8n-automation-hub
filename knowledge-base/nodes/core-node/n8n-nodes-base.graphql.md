<!-- n8n built-in node reference: n8n-nodes-base.graphql | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.graphql -->

[GraphQL](https://graphql.org/) is an open-source data query and manipulation language for APIs, and a runtime for fulfilling queries with existing data. Use the GraphQL node to query a GraphQL endpoint.

## Node parameters

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

### Authentication

Select the type of authentication to use. n8n recommends using **Predefined Credential Type** when it's available for the service you want to connect to. It offers an easier way to set up and manage credentials, compared to configuring generic credentials manually.

If you select **Predefined Credential Type**, a **Credential Type** parameter appears. Select the app or service you want to use, then select an existing credential for it or create a new one. Refer to [Custom API operations](https://docs.n8n.io/integrations/builtin/custom-api-actions-for-existing-nodes) for more information.

If you select any other authentication method except **None**, a **Credential for <selected-auth-type>** parameter appears for you to select an existing or create a new authentication credential for that authentication type.

### HTTP Request Method

Select the underlying HTTP Request method the node should use. Choose from:

* **GET**
* **POST**: If you select this method, you'll also need to select the **Request Format** the node should use for the query payload. Choose from:
    * **GraphQL (Raw)**
    * **JSON**

### Endpoint

Enter the GraphQL Endpoint you'd like to hit.

### Ignore SSL Issues

When you turn on this control, n8n ignores SSL certificate validation failure.

### Query

Enter the GraphQL query you want to execute.

Refer to [Related Resources](#related-resources) for information on writing your query.

### Response Format

Select the format you'd like to receive query results in. Choose between:

* **JSON**
* **String**: If you select this format, enter a **Response Data Property Name** to define the property the string is written to.

## Headers

Enter any **Headers** you want to pass as part of the query as **Name** / **Value** pairs.

## Templates and examples

[Browse GraphQL integration templates](https://n8n.io/integrations/graphql) or [search all templates](https://n8n.io/workflows/)

## Related resources

To use the GraphQL node, you need to understand GraphQL query language. GraphQL have their own [Introduction to GraphQL](https://graphql.org/learn/) tutorial.
