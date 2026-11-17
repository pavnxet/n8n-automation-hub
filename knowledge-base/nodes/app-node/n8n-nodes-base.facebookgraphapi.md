<!-- n8n built-in node reference: n8n-nodes-base.facebookgraphapi | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.facebookgraphapi -->

Use the Facebook Graph API node to automate work in Facebook Graph API, and integrate Facebook Graph API with other applications. n8n has built-in support for a wide range of Facebook Graph API features, including using queries GET POST DELETE for several parameters like host URL, request methods and much more.

On this page, you'll find a list of operations the Facebook Graph API node supports and links to more resources.

> **Credentials:**
> Refer to [Facebook Graph API credentials](https://docs.n8n.io/integrations/builtin/credentials/facebookgraph) for guidance on setting up authentication.

## Operations

* **Default**
    * GET
    * POST
    * DELETE 
* **Video Uploads**
    * GET
    * POST
    * DELETE 

### Parameters

> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.

* **Host URL**: The host URL for the request. The following options are available:
    * **Default**: Requests are passed to the `graph.facebook.com` host URL. Used for the majority of requests.
    * **Video**: Requests are passed to the `graph-video.facebook.com` host URL. Used for video upload requests only.
* **HTTP Request Method**: The method to be used for this request, from the following options:
    * **GET**
    * **POST**
    * **DELETE**
* **Graph API Version**: The version of the [Facebook Graph API](https://developers.facebook.com/docs/graph-api/changelog) to be used for this request.
* **Node**: The node on which to operate, for example `//feed`. Read more about it in the [official Facebook Developer documentation](https://developers.facebook.com/docs/graph-api/using-graph-api).
* **Edge**: Edge of the node on which to operate. Edges represent collections of objects which are attached to the node.
* **Ignore SSL Issues**: Toggle to still download the response even if SSL certificate validation isn't possible.
* **Send Binary File**: Available for `POST` operations. If enabled binary data is sent as the body. Requires setting the following:
    * **Input Binary Field**: Name of the binary property which contains the data for the file to be uploaded.

## Templates and examples

[Browse Facebook Graph API node documentation integration templates](https://n8n.io/integrations/facebook-graph-api) or [search all templates](https://n8n.io/workflows/)
