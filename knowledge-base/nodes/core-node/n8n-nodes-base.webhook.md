<!-- n8n built-in node reference: n8n-nodes-base.webhook | source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook -->

Use the Webhook node to create [webhooks](https://en.wikipedia.org/wiki/Webhook), which can receive data from apps and services when an event occurs. It's a trigger node, which means it can start an n8n workflow. This allows services to connect to n8n and run a workflow.

You can use the Webhook node as a trigger for a workflow when you want to receive data and run a workflow based on the data. The Webhook node also supports returning the data generated at the end of a workflow. This makes it useful for building a workflow to process data and return the results, like an API endpoint.

The webhook allows you to trigger workflows from services that don't have a dedicated app trigger node.

## Workflow development process

n8n provides different **Webhook URL**s for testing and production. The testing URL includes an option to **Listen for test event**. Refer to [Workflow development](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/workflow-development) for more information on building, testing, and shifting your Webhook node to production.

## Node parameters

Use these parameters to configure your node.

### Webhook URLs

The Webhook node has two **Webhook URLs**: test and production. n8n displays the URLs at the top of the node panel.

Select **Test URL** or **Production URL** to toggle which URL n8n displays.

<figure><figcaption>Sample Webhook URLs in the Webhook node's Parameters tab</figcaption></figure>

* **Test**: n8n registers a test webhook when you select **Listen for Test Event** or **Execute workflow**, if the workflow isn't active. When you call the webhook URL, n8n displays the data in the workflow.
* **Production**: n8n registers a production webhook when you publish the workflow. When using the production URL, n8n doesn't display the data in the workflow. You can still view workflow data for a production execution: select the **Executions** tab in the workflow, then select the workflow execution you want to view.

### HTTP Method

The Webhook node supports standard [HTTP Request Methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods):

* DELETE
* GET
* HEAD
* PATCH
* POST
*   PUT

    
> **Note:** Webhook max payload The webhook maximum payload size is 16MB. If you're self-hosting n8n, you can change this using the endpoint environment variable N8N_PAYLOAD_SIZE_MAX .

### Path

By default, this field contains a randomly generated webhook URL path, to avoid conflicts with other webhook nodes.

You can manually specify a URL path, including adding route parameters. For example, you may need to do this if you use n8n to prototype an API and want consistent endpoint URLs.

The **Path** field can take the following formats:

* `/:variable`
* `/path/:variable`
* `/:variable/path`
* `/:variable1/path/:variable2`
* `/:variable1/:variable2`

### Supported authentication methods

You can require authentication for any service calling your webhook URL. Choose from these authentication methods:

* Basic auth
* Header auth
* JWT auth
* **n8n User Auth (OAuth2)**
* None

Refer to [Webhook credentials](https://docs.n8n.io/integrations/builtin/credentials/webhook) for more information on setting up the Basic auth, Header auth, and JWT auth credential types.

#### Using n8n User Auth (OAuth2)

Only users logged in to this n8n instance can call the webhook. The caller must send an OAuth2 bearer token issued by this instance. n8n resolves the token to the calling user and runs the execution as that user. [End-user credentials](https://app.gitbook.com/s/wMJrGrimpx3PxCJpUswm/manage-credentials/end-user-credentials) resolve to the calling user's connected accounts under this mode.

Requests without a bearer token are handled as follows:

* A GET request from a browser is redirected to the n8n sign-in page. After the user signs in and gives consent, n8n redirects the browser back to the webhook URL and runs the workflow.
* Any other request receives a 401 response. Only GET requests can be redirected.

The **OAuth2 Client** option in [Node options](#node-options) controls this behavior.

When you select **n8n User Auth (OAuth2)**, a **Require Workflow Execute Permission** toggle appears. It is on by default. When it is on, the calling user must also have permission to execute the workflow in the project it belongs to. Users who are logged in but lack execute permission on the workflow can't trigger it. A request with a bearer token from such a user receives a 403 response.

#### Calling a webhook that uses n8n User Auth (OAuth2)

n8n is the OAuth2 authorization server for the webhook. How the caller gets a bearer token depends on the caller:

* **A browser:** Open the webhook URL. n8n redirects you to the sign-in page and the consent screen, then runs the workflow. This works for GET requests only, and only when **OAuth2 Client** is **Auto-Detect** or **Browser (Virtual Client)**.
* **A client that supports OAuth 2.1 discovery:** Set **OAuth2 Client** to **Bearer Token Only**, or use **Auto-Detect** for non-browser requests, then send the request without a token. The 401 response carries a `WWW-Authenticate` header with a `resource_metadata` URL. Clients that support protected resource metadata, dynamic client registration, and PKCE use that URL to complete sign-in and consent without manual setup.
* **Your own script or service:** Complete the OAuth2 authorization code flow against the n8n instance:
  1. Read the authorization server metadata at `https://<your-n8n-url>/.well-known/oauth-authorization-server`. It lists the registration, authorization, and token endpoints.
  2. Register a client at the registration endpoint, or reuse a client you registered before.
  3. Send the user to the authorization endpoint with PKCE (`S256`) and the `resource` parameter set to the webhook URL plus `?method=<HTTP method>`, for example `https://<your-n8n-url>/webhook/my-path?method=POST`. The user signs in and gives consent.
  4. Exchange the authorization code at the token endpoint for an access token and a refresh token.
  5. Call the webhook with the `Authorization: Bearer ` header.

A token is bound to the webhook trigger it was issued for. A token issued for another trigger, or for the instance's MCP server, receives a 401 response.

### Respond

* **Immediately**: The Webhook node returns the response code and the message **Workflow got started**.
* **When Last Node Finishes**: The Webhook node returns the response code and the data output from the last node executed in the workflow.
* **Using 'Respond to Webhook' Node**: The Webhook node responds as defined in the [Respond to Webhook](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.respondtowebhook) node.
* **Streaming response**: Enables real-time data streaming back to the user as the workflow processes. Requires nodes with streaming support in the workflow (for example, the [AI agent](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent) node).

### Response Code

Customize the [HTTP response code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) that the Webhook node returns upon successful execution. Select from common response codes or create a custom code.

### Response Data

Choose what data to include in the response body:

* **All Entries**: The Webhook returns all the entries of the last node in an array.
* **First Entry JSON**: The Webhook returns the JSON data of the first entry of the last node in a JSON object.
* **First Entry Binary**: The Webhook returns the binary data of the first entry of the last node in a binary file.
* **No Response Body**: The Webhook returns without a body.

Applies only to **Respond > When Last Node Finishes**.

## Node options

Select **Add Option** to view more configuration options. The available options depend on your node parameters. Refer to the table for option availability.

* **Allowed Origins (CORS)**: Set the permitted cross-origin domains. Enter a comma-separated list of URLs allowed for cross-origin non-preflight requests. Use `*` (default) to allow all origins.
* **Binary Property**: Enabling this setting allows the Webhook node to receive binary data, such as an image or audio file. Enter the name of the binary property to write the data of the received file to.
* **Ignore Bots**: Ignore requests from bots like link previewers and web crawlers.
* **IP(s) Allowlist**: Enable this to limit who (or what) can invoke a Webhook trigger URL. Enter a comma-separated list of allowed IP addresses. Access from IP addresses outside the allowlist throws a 403 error. If left blank, all IP addresses can invoke the webhook trigger URL.
* **No Response Body**: Enable this to prevent n8n sending a body with the response.
* **OAuth2 Client**: How n8n handles a request without a bearer token when **Authentication** is **n8n User Auth (OAuth2)**. **Auto-Detect** (default) redirects browser navigations through the n8n sign-in page and requires a bearer token from everything else. **Bearer Token Only** always requires a bearer token and never redirects. **Browser (Virtual Client)** always redirects GET requests without a bearer token through the n8n sign-in page. Only GET requests can be redirected. Webhook nodes with a version below 2.2 keep the **Bearer Token Only** behavior until you set this option.
* **Only Run If**: An expression evaluated against the incoming request. The workflow only runs if the expression returns `true`. Use `$json` to access the request as `{ body, headers, params, query }`. For example, `{{ $json.body.campaign_id === 'user-research-invite' }}`. Requests that don't match receive a 200 response without creating an execution. If the expression fails to evaluate, n8n logs a warning and lets the request through rather than blocking it. This runs after IP allowlist and authentication checks, and applies to both test and production webhook URLs.
* **Raw Body**: Specify that the Webhook node will receive data in a raw format, such as JSON or XML.
* **Response Content-Type**: Choose the format for the webhook body.
* **Response Data**: Send custom data with the response.
* **Response Headers**: Send extra headers in the Webhook response. Refer to [MDN Web Docs | Response header](https://developer.mozilla.org/en-US/docs/Glossary/Response_header) to learn more about response headers.
* **Property Name**: by default, n8n returns all available data. You can choose to return a specific JSON key, so that n8n returns the value.

| Option                 | Required node configuration                                                           |
| ---------------------- | ------------------------------------------------------------------------------------- |
| Allowed Origins (CORS) | Any                                                                                   |
| Binary Property        | Either:
HTTP Method > POST
HTTP Method > PATCH
HTTP Method > PUT      |
| Ignore Bots            | Any                                                                                   |
| IP(s) Allowlist        | Any                                                                                   |
| Only Run If           | Any                                                                                   |
| Property Name          | Both:
Respond > When Last Node Finishes
Response Data > First Entry JSON |
| No Response Body       | Respond > Immediately                                                                 |
| OAuth2 Client          | Authentication > n8n User Auth (OAuth2)                                               |
| Raw Body               | Any                                                                                   |
| Response Code          | Any except Respond > Using 'Respond to Webhook' Node                                  |
| Response Content-Type  | Both:
Respond > When Last Node Finishes
Response Data > First Entry JSON |
| Response Data          | Respond > Immediately                                                                 |
| Response Headers       | Any                                                                                   |

## How n8n secures HTML responses

> **Feature availability:**
> Automatic wrapping of HTML responses to webhooks in `<iframe>` tags was introduced in n8n 1.103.0.

Starting with n8n 1.103.0, n8n automatically wraps HTML responses to webhooks in `<iframe>` tags. This is a security mechanism to protect the instance users.

This has the following implications:

* HTML renders in a sandboxed iframe instead of directly in the parent document.
* JavaScript code that attempts to access the top-level window or local storage will fail.
* Authentication headers aren't available in the sandboxed iframe (for example, basic auth). You need to use an alternative approach, like embedding a short-lived access token within the HTML.
* Relative URLs (for example, `<form action="/">`) won't work. Use absolute URLs instead.

## Templates and examples

[Browse n8n-nodes-base.webhook integration templates](https://n8n.io/integrations/webhook) or [search all templates](https://n8n.io/workflows/)

## FAQ

### How do I trigger a workflow from an external event?

Add the Webhook node as your trigger. It creates a [webhook URL](#webhook-urls) that receives data from apps and services when an event occurs, then starts your workflow with that data. It's useful for services that don't have a dedicated app trigger node.

### What's the difference between the test and production webhook URLs?

The node has two [webhook URLs](#webhook-urls). The **test** URL works when you select **Listen for Test Event**, and it shows the incoming data in the editor. The **production** URL registers when you publish the workflow, and it doesn't display data in the editor. You can view production runs in the workflow's **Executions** tab.

### How do I secure a webhook?

Require authentication in [Supported authentication methods](#supported-authentication-methods). You can use Basic auth, Header auth, or JWT auth for any service calling the URL, or n8n User Auth (OAuth2) to limit callers to logged-in users of this n8n instance. You can also limit callers with the **IP(s) Allowlist** node option. Refer to [Webhook credentials](https://docs.n8n.io/integrations/builtin/credentials/webhook).

## Common issues

For common questions or issues and suggested solutions, refer to [Common issues](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/common-issues).

---

## Webhook node common issues

## Common issues

Here are some common issues and questions for the [Webhook node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook) and suggested solutions.

### Listen for multiple HTTP methods

By default, the Webhook node accepts calls that use a single method. For example, it can accept GET or POST requests, but not both. If you want to accept calls using multiple methods:

1. Open the node **Settings**.
2. Turn on **Allow Multiple HTTP Methods**.
3. Return to **Parameters**. By default, the node now accepts GET and POST calls. You can add other methods in the **HTTP Methods** field.

The Webhook node has an output for each method, so you can perform different actions depending on the method.

### Use the HTTP Request node to trigger the Webhook node

The [HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest) node makes HTTP requests to the URL you specify.

1. Create a new workflow.
2. Add the HTTP Request node to the workflow.
3. Select a method from the **Request Method** dropdown list. For example, if you select GET as the **HTTP method** in your Webhook node, select GET as the request method in the HTTP Request node.
4. Copy the URL from the Webhook node, and paste it in the **URL** field in the HTTP Request node.
5. If using the test URL for the webhook node: execute the workflow with the Webhook node.
6. Execute the HTTP Request node.

### Use curl to trigger the Webhook node

You can use [curl](https://curl.se/) to make HTTP requests that trigger the Webhook node.

> **Note:** In the examples, replace `<https://your-n8n.url/webhook/path>` with your webhook URL.\
> The examples make GET requests. You can use whichever HTTP method you set in **HTTP Method**.

Make an HTTP request without any parameters:

```sh
curl --request GET <https://your-n8n.url/webhook/path>
```

Make an HTTP request with a body parameter:

```sh
curl --request POST <https://your-n8n.url/webhook/path> --data 'key=value'
```

Make an HTTP request with header parameter:

```sh
curl --request GET <https://your-n8n.url/webhook/path> --header 'key=value'
```

Make an HTTP request to send a file:

```sh
curl --request POST <https://your-n8n.url/webhook/path> --form 'key=@/path/to/file'
```

Replace `/path/to/file` with the path of the file you want to send.

### Send a response of type string

By default, the response format is JSON or an array. To send a response of type string:

1. Select **Response Mode** > **When Last Node Finishes**.
2. Select **Response Data** > **First Entry JSON**.
3. Select **Add Option** > **Property Name**.
4. Enter the name of the property that contains the response. This defaults to `data`.
5. Connect an [Edit Fields node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.set) to the Webhook node.
6. In the Edit Fields node, select **Add Value** > **String**.
7. Enter the name of the property in the **Name** field. The name should match the property name from step 4.
8. Enter the string value in the **Value** field.
9. Toggle **Keep Only Set** to on (green).

When you call the Webhook, it sends the string response from the Edit Fields node.

### Test URL versus Production URL

n8n generates two **Webhook URLs** for each Webhook node: a **Test URL** and a **Production URL**.

While building or testing a workflow, use the **Test URL**. Once you're ready to use your Webhook URL in production, use the **Production URL**.

| **URL type**   | **How to trigger**                                                         | **Listening duration**        | **Data shown in editor UI?** |
| -------------- | -------------------------------------------------------------------------- | ----------------------------- | :--------------------------: |
| Test URL       | Select **Listen for test event** and trigger a test event from the source. | 120 seconds                   |               ✅              |
| Production URL | Publish the workflow                                                       | Until workflow is unpublished |               ❌              |

Refer to [Workflow development](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/workflow-development) for more information.

### IP addresses in whitelist are failing to connect

If you're unable to connect from IP addresses in your IP whitelist, check if you are running n8n behind a reverse proxy.

If so, set the `N8N_PROXY_HOPS` [environment variable](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/configure-n8n/basic-configuration/use-environment-variables) to the number of reverse-proxies n8n is running behind.

### Only one webhook per path and method

n8n only permits registering one webhook for each path and HTTP method combination (for example, a `GET` request for `/my-request`). This avoids ambiguity over which webhook should receive requests.

If you receive a message that the path and method you chose are already in use, you can either:

* Unpublish the workflow with the conflicting webhook.
* Change the webhook path and/or method for one of the conflicting webhooks.

### Timeouts on n8n Cloud

n8n Cloud uses Cloudflare to protect against malicious traffic. If your webhook doesn't respond within 100 seconds, the incoming request will fail with a [524 status code](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/).

Because of this, for long-running processes that might exceed this limit, you may need to introduce polling logic by configuring two separate webhooks:

* One webhook to start the long-running process and send an immediate response.
* A second webhook that you can call at intervals to query the status of the process and retrieve the result once it's complete.

---

## Webhook node workflow development documentation

## Workflow development

The [Webhook node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook) works a bit differently from other core nodes. n8n recommends following these processes for building, testing, and using your Webhook node in production.

n8n generates two **Webhook URLs** for each Webhook node: a **Test URL** and a **Production URL**.

### Build and test workflows

While building or testing a workflow, use the **Test** webhook URL.

Using a test webhook ensures that you can view the incoming data in the editor UI, which is useful for debugging. Select **Listen for test event** to register the webhook before sending the data to the test webhook. The test webhook stays active for 120 seconds.

When using the Webhook node on localhost on a [self-hosted](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n) n8n instance, run n8n in tunnel mode:

* [npm with tunnel](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/install-options/install-with-npm#n8n-with-tunnel)
* [Docker with tunnel](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n/install-options/install-with-docker#n8n-with-tunnel)

### Production workflows

When your workflow is ready, switch to using the **Production** webhook URL. You can then publish your workflow, and n8n runs it automatically when an external service calls the webhook URL.

When working with a Production webhook, ensure that you have saved and published the workflow. Data flowing through the webhook isn't visible in the editor UI with the production webhook.

Refer to [Create a workflow](https://app.gitbook.com/s/rPN1zU5jaYNvwH7RzxqA/understand-workflows/create-and-run-workflows) for more information on publishing workflows.
