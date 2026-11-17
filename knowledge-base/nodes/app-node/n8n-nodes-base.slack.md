<!-- n8n built-in node reference: n8n-nodes-base.slack | source: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.slack -->

Use the Slack node to automate work in Slack, and integrate Slack with other applications. n8n has built-in support for a wide range of Slack features, including creating, archiving, and closing channels, getting users and files, as well as deleting messages.

On this page, you'll find a list of operations the Slack node supports and links to more resources.

> **Credentials:**
> Refer to [Slack credentials](https://docs.n8n.io/integrations/credentials/slack) for guidance on setting up authentication.

## Operations

* **Channel**
    * **Archive** a channel.
    * **Close** a direct message or multi-person direct message.
    * **Create** a public or private channel-based conversation.
    * **Get** information about a channel.
    * **Get Many**: Get a list of channels in Slack.
    * **History**: Get a channel's history of messages and events.
    * **Invite** a user to a channel.
    * **Join** an existing channel.
    * **Kick**: Remove a user from a channel.
    * **Leave** a channel.
    * **Member**: List the members of a channel.
    * **Open** or resume a direct message or multi-person direct message.
    * **Rename** a channel.
    * **Replies**: Get a thread of messages posted to a channel.
    * **Sets purpose** of a channel.
    * **Sets topic** of a channel.
    * **Unarchive** a channel.
* **File**
    * **Get** a file.
    * **Get Many**: Get and filter team files.
    * **Upload**: Create or upload an existing file.
* **Message**
    * **Delete** a message
    * **Get permalink**: Get a message's permalink.
    * **Search** for messages
    * **Send** a message
    * **Send and Wait for Response**: Send a message and wait for a response from the recipient before continuing. Approvers can also respond directly inside Slack. Refer to [Approvals in Slack](https://docs.n8n.io/integrations/builtin/app-nodes/approvals) for more information.
    * **Update** a message
* **Reaction**
    * **Add** a reaction to a message.
    * **Get** a message's reactions.
    * **Remove** a reaction from a message.
* **Star**
    * **Add** a star to an item.
    * **Delete** a star from an item.
    * **Get Many**: Get a list of an authenticated user's stars.
* **User**
    * **Get** information about a user.
	* **Get Many**: Get a list of users.
    * **Get User's Profile**.
    * **Get User's Status**.
	* **Update User's Profile**.
* **User Group**
    * **Create** a user group.
    * **Disable** a user group.
    * **Enable** a user group.
    * **Get Many**: Get a list of user groups.
    * **Update** a user group.

## Message search and version-specific behavior

### Search messages

Node version 2.7 and above uses the [Real-time Search API](https://docs.slack.dev/apis/web-api/real-time-search-api/) (`assistant.search.context`) for the **Message > Search** operation. Node version 2.6 and below use the deprecated [`search.messages`](https://api.slack.com/methods/search.messages) endpoint. n8n gates this by node version, so the change doesn't affect existing workflows on node version 2.6 and below.

On node version 2.7 and above:

- **New options**: **Channel Types** (public, private, group DM, DM), **After** and **Before** (date filters), and **Keyword Search Only** (disables semantic search).
- **Semantic search**: by default, Slack may apply semantic search to question-style queries (for example, queries that start with a question word or end with a question mark), so results aren't always strictly literal keyword matches. Enable **Keyword Search Only** to force literal matching. Semantic ranking requires Slack AI (a paid plan).
- **Limit**: **Return All** is removed from node version 2.7 and above. Only **Limit** remains, capped at 50. The endpoint returns 20 results per request and rate limits aggressively (around 10 requests per minute per user), so it isn't built for exhaustive retrieval. Node version 2.6 and below keep **Return All**.
- **Authentication**: the endpoint needs a user token, so use OAuth2 or supply a user token with Access Token authentication. A bot token can't call this endpoint, and the Slack app must have AI features enabled. If you use OAuth2, reconnect your existing credential so it picks up the new `search:read.*` scopes.
- **Output fields**: results use `content`, `message_ts`, `channel_id`, `channel_name`, and `author_name`, instead of the previous `text`, `ts`, `channel`, and `username`.

### Custom Bot Profile Photo

From node version 2.6, the **Message > Send** option **Custom Bot Profile Photo** (custom icon or emoji) is only available with **Access Token** authentication, not OAuth2. It relies on the `chat:write.customize` scope, which is a bot-token-only scope that the OAuth2 user-token path can't use. Node version 2.5 and below still show the option with OAuth2, though Slack ignores it in that case.

## Templates and examples

[Browse Slack node documentation integration templates](https://n8n.io/integrations/slack) or [search all templates](https://n8n.io/workflows/)

## Related resources

Refer to [Slack's documentation](https://api.slack.com/) for more information about the service.

## Required scopes

Once you create a Slack app for your [Slack credentials](https://docs.n8n.io/integrations/credentials/slack), you must add the appropriate scopes to your Slack app for this node to work. Start with the scopes listed in the [Scopes | Slack credentials](https://docs.n8n.io/integrations/credentials/slack#scopes) page.

If those aren't enough, use the table below to look up the resource and operation you want to use, then follow the link to Slack's API documentation to find the correct scopes.

| **Resource** | **Operation**              | **Slack API method**                                                               |
|--------------|----------------------------|------------------------------------------------------------------------------------|
| Channel      | Archive                    | [conversations.archive](https://api.slack.com/methods/conversations.archive)       |
| Channel      | Close                      | [conversations.close](https://api.slack.com/methods/conversations.close)           |
| Channel      | Create                     | [conversations.create](https://api.slack.com/methods/conversations.create)         |
| Channel      | Get                        | [conversations.info](https://api.slack.com/methods/conversations.info)             |
| Channel      | Get Many                   | [conversations.list](https://api.slack.com/methods/conversations.list)             |
| Channel      | History                    | [conversations.history](https://api.slack.com/methods/conversations.history)       |
| Channel      | Invite                     | [conversations.invite](https://api.slack.com/methods/conversations.invite)         |
| Channel      | Join                       | [conversations.join](https://api.slack.com/methods/conversations.join)             |
| Channel      | Kick                       | [conversations.kick](https://api.slack.com/methods/conversations.kick)             |
| Channel      | Leave                      | [conversations.leave](https://api.slack.com/methods/conversations.leave)           |
| Channel      | Member                     | [conversations.members](https://api.slack.com/methods/conversations.members)       |
| Channel      | Open                       | [conversations.open](https://api.slack.com/methods/conversations.open)             |
| Channel      | Rename                     | [conversations.rename](https://api.slack.com/methods/conversations.rename)         |
| Channel      | Replies                    | [conversations.replies](https://api.slack.com/methods/conversations.replies)       |
| Channel      | Set Purpose                | [conversations.setPurpose](https://api.slack.com/methods/conversations.setPurpose) |
| Channel      | Set Topic                  | [conversations.setTopic](https://api.slack.com/methods/conversations.setTopic)     |
| Channel      | Unarchive                  | [conversations.unarchive](https://api.slack.com/methods/conversations.unarchive)   |
| File         | Get                        | [files.info](https://api.slack.com/methods/files.info)                             |
| File         | Get Many                   | [files.list](https://api.slack.com/methods/files.list)                             |
| File         | Upload                     | [files.upload](https://api.slack.com/methods/files.upload)                         |
| Message      | Delete                     | [chat.delete](https://api.slack.com/methods/chat.delete)                           |
| Message      | Get Permalink              | [chat.getPermalink](https://api.slack.com/methods/chat.getPermalink)               |
| Message      | Search                     | Node version 2.7 and above: [assistant.search.context](https://docs.slack.dev/reference/methods/assistant.search.context) (Real-time Search API). Node version 2.6 and below: [search.messages](https://api.slack.com/methods/search.messages) (deprecated). |
| Message      | Send                       | [chat.postMessage](https://api.slack.com/methods/chat.postMessage)                 |
| Message      | Send and Wait for Response | [chat.postMessage](https://api.slack.com/methods/chat.postMessage)                 |
| Message      | Update                     | [chat.update](https://api.slack.com/methods/chat.update)                           |
| Reaction     | Add                        | [reactions.add](https://api.slack.com/methods/reactions.add)                       |
| Reaction     | Get                        | [reactions.get](https://api.slack.com/methods/reactions.get)                       |
| Reaction     | Remove                     | [reactions.remove](https://api.slack.com/methods/reactions.remove)                 |
| Star         | Add                        | [stars.add](https://api.slack.com/methods/stars.add)                               |
| Star         | Delete                     | [stars.remove](https://api.slack.com/methods/stars.remove)                         |
| Star         | Get Many                   | [stars.list](https://api.slack.com/methods/stars.list)                             |
| User         | Get                        | [users.info](https://api.slack.com/methods/users.info)                             |
| User         | Get Many                   | [users.list](https://api.slack.com/methods/users.list)                             |
| User         | Get User's Profile         | [users.profile.get](https://api.slack.com/methods/users.profile.get)               |
| User         | Get User's Status          | [users.getPresence](https://api.slack.com/methods/users.getPresence)               |
| User         | Update User's Profile      | [users.profile.set](https://api.slack.com/methods/users.profile.set)               |
| User Group   | Create                     | [usergroups.create](https://api.slack.com/methods/usergroups.create)               |
| User Group   | Disable                    | [usergroups.disable](https://api.slack.com/methods/usergroups.disable)             |
| User Group   | Enable                     | [usergroups.enable](https://api.slack.com/methods/usergroups.enable)               |
| User Group   | Get Many                   | [usergroups.list](https://api.slack.com/methods/usergroups.list)                   |
| User Group   | Update                     | [usergroups.update](https://api.slack.com/methods/usergroups.update)               |

---

## Approvals

## Approvals in Slack

With the **Message** > **Send and Wait for Response** operation, approvers can approve or decline directly inside Slack. No browser page opens: the workflow resumes as soon as someone responds, and the output records who responded.

### How it differs from link buttons

| What | Link buttons (default) | Approvals in Slack |
|------|------------------------|--------------------|
| Where the decision happens | Opens an n8n page in the browser | One click inside Slack |
| Who can respond | Anyone who can click the link | Only the approvers you list (an empty list lets anyone who can see the message respond). Anyone else gets a private note you can word yourself, and the workflow keeps waiting. |
| Output | `approved` and `respondedAt` | Adds who responded (ID, name, username, and email) plus the channel and message |
| The message after the decision | Unchanged. The buttons stay clickable, but later clicks show a "no action required" page. The first decision stands. | Your choice: show the outcome and remove the buttons (default), remove the buttons only, or leave the message unchanged |
| Security | Signed links: no one can tamper with the URL or its action, but anyone who has the link can respond, and n8n can't tell who clicked | n8n verifies every callback came from Slack (using Slack's request signing) and checks the responder against your approver list |

### Requirements

To approve within Slack, you need:

- Your n8n instance to be reachable from Slack over public HTTPS. Slack calls your instance back when someone responds, so an instance running on localhost won't work.
- A Slack credential, using either an API access token or OAuth2.
- The **Signature Secret** field of your Slack credential must contain your Slack app's signing secret, found in **Settings** > **Basic Information**. Without it, the buttons render but clicks don't resume the workflow.
- **Response Type** set to **Approval**.
- The `users:read` and `users:read.email` scopes. The responder's ID, name, and username come from Slack's interaction payload; the email comes from the Slack API and needs these scopes. Missing scopes just mean the output omits the email. If you use an OAuth2 credential created before this feature existed, reconnect it so it picks up the `users:read.email` scope.

### Set up approvals

#### 1. Create a Slack app and credential

Follow [Using API access token](https://docs.n8n.io/credentials/slack#using-api-access-token) or [Using OAuth2](https://docs.n8n.io/credentials/slack#using-oauth2) to create a Slack app and set up your credential. When you configure your app's scopes, add `users:read` and `users:read.email` so the output can include the responder's email.

#### 2. Turn on Interactivity

1. Go to [Your Apps](https://api.slack.com/apps) in Slack and select the app you want to use.
2. Go to **Features** > **Interactivity & Shortcuts** and turn on **Interactivity**.
3. In **Request URL**, enter `https://<your-n8n-instance>/webhook-waiting-slack`. All workflows on the instance share this one URL. If you changed the `N8N_ENDPOINT_WEBHOOK_WAIT` environment variable, adjust the path to match.
4. Select **Save Changes**.

> **Note:** Slack allows one **Request URL** per app, so one Slack app serves one n8n instance.

#### 3. Add the signing secret to your credential

1. In your Slack app, go to **Settings** > **Basic Information** and copy the **Signing Secret** from the **App Credentials** section.
2. In n8n, paste it into the **Signature Secret** field of your Slack credential.

n8n uses the signing secret to verify that each callback comes from Slack. n8n rejects callbacks that fail verification, and the workflow keeps waiting.

#### 4. Configure the node

In the Slack node, select the **Message** resource with the **Send and Wait for Response** operation, and set **Response Type** to **Approval**. The settings below then appear under the **Advanced Interactivity** section header.

- **Capture Who Responded**: turn this on to switch the approval buttons to Slack interactive buttons and record who responded. The remaining settings appear once it's on.
- **Restrict Who Can Approve**: select the users allowed to act. You can also specify user IDs with an expression. Anyone not on the list who clicks gets a private notice, and the workflow keeps waiting.
- **Unauthorized Reply**: the private (ephemeral) message shown to someone who clicks but isn't on the approver list. Defaults to `You are not authorized to respond to this request.`
- **After Decision**: what happens to the original Slack message once someone approves or declines.
    - **Show Outcome and Remove Buttons** (default): removes the buttons and adds a line naming the decision and the responder.
    - **Remove Buttons Only**: removes the buttons without adding an outcome line.
    - **Keep Message Unchanged**: leaves the message as sent, buttons included. Later clicks don't change the recorded decision, which is the first one.

If you leave the approver list empty, anyone who can see the message can approve or decline. In a channel, that's every member. The list controls who can respond, not who can see the request, so post sensitive approvals to a private channel or direct message.

#### 5. Test it

Execute the workflow, select **Approve** in Slack, and check the node output.

### Node output

When someone responds in Slack, the node outputs the decision and the responder:

```json
{
	"data": {
		"approved": true,
		"respondedAt": "2025-07-13T12:34:56.000Z",
		"channel": "C0123ABC456",
		"messageId": "1752407696.123456",
		"responder": {
			"id": "U0123ABC456",
			"name": "Jo Doe",
			"username": "jo.doe",
			"email": "jo@example.com",
			"source": "slack"
		}
	}
}
```

With link buttons, the output contains only `approved` and `respondedAt`.

### When you get link buttons instead

The node behaves as before, sending buttons that open an n8n confirmation page, when any of these apply:

- **Response Type** is **Free Text** or **Custom Form**.
- **Capture Who Responded** is off.

Existing workflows keep working unchanged.

### Troubleshooting

- **The buttons don't do anything, or Slack shows a warning**: the **Request URL** is wrong, your instance isn't publicly reachable over HTTPS, or the **Signature Secret** is missing or wrong. Slack shows the same warning for a rejected callback as for an unreachable URL.
- **Someone gets a "not authorized" reply**: that user isn't listed in **Restrict Who Can Approve**. The wording comes from **Unauthorized Reply**.
- **The workflow never resumes although someone responded**: the **Signature Secret** is missing or doesn't match your app's **Signing Secret**. n8n rejects callbacks it can't verify, and the workflow keeps waiting.
