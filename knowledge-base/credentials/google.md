<!-- n8n built-in node reference: google | source: https://docs.n8n.io/integrations/builtin/credentials/google -->

This section contains:

* [OAuth2 single service](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service): Create an OAuth2 credential for a specific service node, such as the Gmail node. Two options exist:
  * [Managed OAuth2](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#managed-oauth2): Sign in with Google directly on n8n, with no setup required on the Google Cloud Console. Available for n8n Cloud users only, for certain Google nodes.
  * [Custom OAuth2](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#custom-oauth2): Configure an OAuth2 app in the Google Cloud Console and connect it to your n8n credential.
* [OAuth2 API (generic)](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic): Create an OAuth2 credential for use with [custom operations](https://docs.n8n.io/integrations/builtin/custom-api-actions-for-existing-nodes).
* [Service Account](https://docs.n8n.io/integrations/builtin/credentials/google/service-account): Create a [Service Account](https://cloud.google.com/iam/docs/service-account-overview) credential for some specific service nodes.
* [Google PaLM and Gemini](https://docs.n8n.io/integrations/builtin/credentials/googleai): Get a Google Gemini/Google PaLM API key.

## OAuth2 and Service Account

Google service nodes support two authentication methods:

* [OAuth2](https://developers.google.com/identity/protocols/oauth2): Recommended because it's more widely available and easier to set up.
* [Service Account](https://cloud.google.com/iam/docs/understanding-service-accounts): Refer to the [Google documentation: Understanding service accounts](https://cloud.google.com/iam/docs/understanding-service-accounts) for guidance on when you need a service account.

### Managed OAuth2 for n8n Cloud users

> **Feature availability:**
> Managed OAuth2 for the Google nodes listed below is available on:
> - **n8n Cloud:** All plans
> It isn't available on self-hosted. For self-hosted, configure your own OAuth2 credentials instead.
> 

## Compatible nodes

Once configured, you can use your credentials to authenticate the following nodes. Most nodes are compatible with OAuth2 authentication. n8n has limited support for Service Account authentication.

| Node                                                                                            | OAuth | Service Account |
| ----------------------------------------------------------------------------------------------- | :---: | :-------------: |
| [Google Ads](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googleads)                                       |   ✅   |        ❌        |
| [Gmail](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.gmail)                                                  |   ✅   |        ⚠️       |
| [Google Analytics](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googleanalytics)                           |   ✅   |        ❌        |
| [Google BigQuery](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlebigquery)                             |   ✅   |        ✅        |
| [Google Books](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlebooks)                                   |   ✅   |        ✅        |
| [Google Calendar](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecalendar)                               |   ✅   |        ❌        |
| [Google Chat](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlechat)                                     |   ✅   |        ✅        |
| [Google Cloud Storage](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecloudstorage)                    |   ✅   |        ✅        |
| [Google Contacts](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecontacts)                             |   ✅   |        ❌        |
| [Google Cloud Firestore](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecloudfirestore)                |   ✅   |        ✅        |
| [Google Cloud Natural Language](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecloudnaturallanguage)   |   ✅   |        ❌        |
| [Google Cloud Realtime Database](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecloudrealtimedatabase) |   ✅   |        ❌        |
| [Google Docs](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googledocs)                                     |   ✅   |        ✅        |
| [Google Drive](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googledrive)                                     |   ✅   |        ✅        |
| [Google Drive Trigger](https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.googledrivetrigger)                  |   ✅   |        ✅        |
| [Google Perspective](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googleperspective)                       |   ✅   |        ❌        |
| [Google Sheets](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets)                                   |   ✅   |        ✅        |
| [Google Slides](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googleslides)                                 |   ✅   |        ✅        |
| [Google Tasks](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googletasks)                                   |   ✅   |        ❌        |
| [Google Translate](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googletranslate)                           |   ✅   |        ✅        |
| [Google Workspace Admin](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.gsuiteadmin)                         |   ✅   |        ❌        |
| [YouTube](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.youtube)                                            |   ✅   |        ❌        |

> **Gmail and Service Accounts:**
> Google technically supports Service Accounts for use with Gmail, but it requires enabling domain-wide delegation, which Google discourages, and its behavior can be inconsistent.
> n8n recommends using OAuth2 with the Gmail node.

---

## Google OAuth2 generic

## Google OAuth2 generic

This document contains instructions for creating a generic Google OAuth2 API credential for use with [custom operations](https://docs.n8n.io/integrations/builtin/custom-api-actions-for-existing-nodes).

### Prerequisites

* Create a [Google Cloud](https://cloud.google.com/) account.

### Set up OAuth

There are five steps to connecting your n8n credential to Google services:

1. [Create a Google Cloud Console project](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic#create-a-google-cloud-console-project).
2. [Enable APIs](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic#enable-apis).
3. [Configure your OAuth consent screen](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic#configure-your-oauth-consent-screen).
4. [Create your Google OAuth client credentials](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic#create-your-google-oauth-client-credentials).
5. [Finish your n8n credential](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic#finish-your-n8n-credential).

#### Create a Google Cloud Console project

First, create a Google Cloud Console project. If you already have a project, jump to the [next section](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic#enable-apis):

#### Enable APIs

With your project created, enable the APIs you'll need access to:

#### Configure your OAuth consent screen

If you haven't used OAuth in your Google Cloud project before, you'll need to [configure the OAuth consent screen](https://developers.google.com/workspace/guides/configure-oauth-consent):

1.  Access your [Google Cloud Console - Library](https://console.cloud.google.com/apis/library). Make sure you're in the correct project.

    <figure><figcaption>Check the project dropdown in the Google Cloud top navigation</figcaption></figure>
2. Open the left navigation menu and go to **APIs & Services > OAuth consent screen**. Google will redirect you to the Google Auth Platform overview page.
3. Select **Get started** on the **Overview** tab to begin configuring OAuth consent.
4. Enter an **App name** and **User support email** to include on the Oauth screen. Select **Next** to continue.
5.  For the **Audience**, select **Internal** for user access within your organization's Google workspace or **External** for any user with a Google account. Refer to Google's [User type documentation](https://support.google.com/cloud/answer/15549945?sjid=17061891731152303663-EU#user-type) for more information on user types. Select **Next** to continue.

    > **Testing mode and test users:**
> If you select **External**, your app will default to Testing mode. In this mode, only Google accounts you manually add as test users can complete the OAuth flow — everyone else will see an "access denied" screen. See [Google hasn't verified this app](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic#google-hasnt-verified-this-app) to learn how to add them.
6. Select the **Email addresses** Google should use to contact you about changes to your project. Select **Next** to continue.
7. Read and accept the Google's User Data Policy. Select **Continue** and then select **Create**.
8. In the left-hand menu, select **Branding**.
9. In the **Authorized domains** section, select **Add domain**:
   * If you're using n8n's Cloud service, add `n8n.cloud`
   * If you're [self-hosting](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n), add the domain of your n8n instance.
10. Select **Save** at the bottom of the page.

#### Create your Google OAuth client credentials

Next, create the OAuth client credentials in Google:

1. Access your [Google Cloud Console](https://console.cloud.google.com/). Make sure you're in the correct project.
2. In the **APIs & Services** section, select [**Credentials**](https://console.cloud.google.com/apis/credentials).
3. Select **+ Create credentials** > **OAuth client ID**.
4. In the **Application type** dropdown, select **Web application**.
5. Google automatically generates a **Name**. Update the **Name** to something you'll recognize in your console.
6.  From your n8n credential, copy the **OAuth Redirect URL**. Paste it into the **Authorized redirect URIs** in Google Console.

    > **OAuth redirect URL for self-hosting:**
> If you're running n8n on your local machine, you don't need a public domain, SSL certificate, or port forwarding to use Google OAuth. Google allows localhost as a valid redirect URI for development purposes. Your n8n OAuth redirect URL will look something like this: `http://localhost:5678/rest/oauth2-credential/callback` For more details on acceptable redirect URIs, refer to [Google's redirect URI documentation](https://support.google.com/cloud/answer/15549257?hl=en#zippy=%2Cweb-applications).
7. Select **Create**.

#### Finish your n8n credential

With the Google project and credentials fully configured, finish the n8n credential:

1. From Google's **OAuth client created** modal, copy the **Client ID**. Enter this in your n8n credential.
2. From the same Google modal, copy the **Client Secret**. Enter this in your n8n credential.
3.  You must provide the scopes for this credential. Refer to [Scopes](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic#scopes) for more information. Enter multiple scopes in a space-separated list, for example:

    ```
    https://www.googleapis.com/auth/gmail.labels https://www.googleapis.com/auth/gmail.addons.current.action.compose
    ```
4. In n8n, select **Sign in with Google** to complete your Google authentication.
5. **Save** your new credentials.

### Video

The following video demonstrates the steps described above:

[Embedded content](https://www.youtube.com/embed/FBGtpWMTppw)

### Scopes

Google services have one or more possible access scopes. A scope limits what a user can do. Refer to [OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes) for a list of scopes for all services.

n8n doesn't support all scopes. When creating a generic Google OAuth2 API credential, you can enter scopes from the **Supported scopes** list below. If you enter a scope that n8n doesn't already support, it won't work.

<details>

<summary>Supported scopes</summary>

| Service                                     | Available scopes                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Gmail                                       | `https://www.googleapis.com/auth/gmail.labels``https://www.googleapis.com/auth/gmail.addons.current.action.compose``https://www.googleapis.com/auth/gmail.addons.current.message.action``https://mail.google.com/``https://www.googleapis.com/auth/gmail.modify``https://www.googleapis.com/auth/gmail.compose` |
| Google Ads                                  | `https://www.googleapis.com/auth/adwords`                                                                                                                                                                                                                                                                                                                                                                           |
| Google Analytics                            | `https://www.googleapis.com/auth/analytics``https://www.googleapis.com/auth/analytics.readonly`                                                                                                                                                                                                                                                                                                 |
| Google BigQuery                             | `https://www.googleapis.com/auth/bigquery`                                                                                                                                                                                                                                                                                                                                                                          |
| Google Books                                | `https://www.googleapis.com/auth/books`                                                                                                                                                                                                                                                                                                                                                                             |
| Google Calendar                             | `https://www.googleapis.com/auth/calendar``https://www.googleapis.com/auth/calendar.events`                                                                                                                                                                                                                                                                                                     |
| Google Cloud
Natural Language     | `https://www.googleapis.com/auth/cloud-language``https://www.googleapis.com/auth/cloud-platform`                                                                                                                                                                                                                                                                                                |
| Google Cloud
Storage              | `https://www.googleapis.com/auth/cloud-platform``https://www.googleapis.com/auth/cloud-platform.read-only``https://www.googleapis.com/auth/devstorage.full_control``https://www.googleapis.com/auth/devstorage.read_only``https://www.googleapis.com/auth/devstorage.read_write`                                                    |
| Google Contacts                             | `https://www.googleapis.com/auth/contacts`                                                                                                                                                                                                                                                                                                                                                                          |
| Google Docs                                 | `https://www.googleapis.com/auth/documents``https://www.googleapis.com/auth/drive``https://www.googleapis.com/auth/drive.file`                                                                                                                                                                                                                                              |
| Google Drive                                | `https://www.googleapis.com/auth/drive``https://www.googleapis.com/auth/drive.appdata``https://www.googleapis.com/auth/drive.photos.readonly`                                                                                                                                                                                                                               |
| Google Firebase
Cloud Firestore   | `https://www.googleapis.com/auth/datastore``https://www.googleapis.com/auth/firebase`                                                                                                                                                                                                                                                                                                           |
| Google Firebase
Realtime Database | `https://www.googleapis.com/auth/userinfo.email``https://www.googleapis.com/auth/firebase.database``https://www.googleapis.com/auth/firebase`                                                                                                                                                                                                                               |
| Google Perspective                          | `https://www.googleapis.com/auth/userinfo.email`                                                                                                                                                                                                                                                                                                                                                                    |
| Google Sheets                               | `https://www.googleapis.com/auth/drive.file``https://www.googleapis.com/auth/spreadsheets`                                                                                                                                                                                                                                                                                                      |
| Google Slide                                | `https://www.googleapis.com/auth/drive.file``https://www.googleapis.com/auth/presentations`                                                                                                                                                                                                                                                                                                     |
| Google Tasks                                | `https://www.googleapis.com/auth/tasks`                                                                                                                                                                                                                                                                                                                                                                             |
| Google Translate                            | `https://www.googleapis.com/auth/cloud-translation`                                                                                                                                                                                                                                                                                                                                                                 |
| GSuite Admin                                | `https://www.googleapis.com/auth/admin.directory.group``https://www.googleapis.com/auth/admin.directory.user``https://www.googleapis.com/auth/admin.directory.domain.readonly``https://www.googleapis.com/auth/admin.directory.userschema.readonly`                                                                                                     |

</details>

### Troubleshooting

#### Google hasn't verified this app

#### Google Cloud app becoming unauthorized

#### redirect\_uri\_mismatch

This error means the redirect URI n8n is sending doesn't match any of the URIs registered in your Google Cloud Console OAuth client.

**Fix:** Copy the **OAuth Redirect URL** from your n8n credential panel and paste it exactly — including the protocol (`http` or `https`) and port number — into the **Authorized redirect URIs** field of your Google OAuth client.

#### Access denied / "app not verified"

This usually happens when your app is still in Testing mode and the Google account you're trying to authenticate with hasn't been added as a test user.

**Fix:** Go to **APIs & Services** > **OAuth consent screen** > **Test users** and add the account you're trying to use.

#### invalid\_client

This error typically means the Client ID or Client Secret in your n8n credential doesn't match what's in Google Cloud Console.

**Fix:** Go back to your OAuth client in Google Cloud Console, copy both values fresh, and re-enter them in n8n. Watch out for accidental spaces when copying.

---

## Google OAuth2 single service

## Google OAuth2 single service

This document contains instructions for creating a Google credential for a single service. They're also available as a [video](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#video).

### Prerequisites

* Create a [Google Cloud](https://cloud.google.com/) account.

### Managed OAuth2

n8n Cloud users can use **Managed OAuth2** for the following nodes:

To use **Managed OAuth2**, click **Sign in with Google** in the credentials screen. You don't need any more setup in the Google Cloud Console or elsewhere.

![n8n credential screen with a Sign in with Google button and a dropdown to switch to Custom OAuth2](https://docs.n8n.io/integrations/.gitbook/assets/managed-oauth.png)

If you prefer to use Custom OAuth2, use the dropdown to change the authentication type.

### Custom OAuth2

Managed OAuth2 isn't available for self-hosted n8n users, nor for Google nodes not listed [above](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#managed-oauth2). You must create a custom OAuth2 single service credential. This means creating an app in the Google Cloud Console and connecting it to n8n with a Client ID and Client Secret.

The rest of this document covers the full process.

### Set up Custom OAuth2

Follow five steps to connect your n8n credential to Google services:

1. [Create a Google Cloud Console project](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#create-a-google-cloud-console-project).
2. [Enable APIs](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#enable-apis).
3. [Configure your OAuth consent screen](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#configure-your-oauth-consent-screen).
4. [Create your Google OAuth client credentials](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#create-your-google-oauth-client-credentials).
5. [Finish your n8n credential](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#finish-your-n8n-credential).

#### Create a Google Cloud Console project

First, create a Google Cloud Console project. If you already have a project, jump to the [next section](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service#enable-apis):

#### Enable APIs

With your project created, enable the APIs you'll need access to:

#### Configure your OAuth consent screen

If you haven't used OAuth in your Google Cloud project before, you'll need to [configure the OAuth consent screen](https://developers.google.com/workspace/guides/configure-oauth-consent):

1.  Access your [Google Cloud Console - Library](https://console.cloud.google.com/apis/library). Make sure you're in the correct project.

    <figure><figcaption>Check the project dropdown in the Google Cloud top navigation</figcaption></figure>
2. Open the left navigation menu and go to **APIs & Services > OAuth consent screen**. Google will redirect you to the Google Auth Platform overview page.
3. Select **Get started** on the **Overview** tab to begin configuring OAuth consent.
4. Enter an **App name** and **User support email** to include on the Oauth screen. Select **Next** to continue.
5.  For the **Audience**, select **Internal** for user access within your organization's Google workspace or **External** for any user with a Google account. Refer to Google's [User type documentation](https://support.google.com/cloud/answer/15549945?sjid=17061891731152303663-EU#user-type) for more information on user types. Select **Next** to continue.

    
> **Note:** Testing mode and test users If you select External , your app will default to Testing mode. In this mode, only Google accounts you manually add as test users can complete the OAuth flow. Everyone else sees an "access denied" screen. See Google hasn't verified this app to learn how to add them.

6. Select the **Email addresses** Google should use to contact you about changes to your project. Select **Next** to continue.
7. Read and accept the Google's User Data Policy. Select **Continue** and then select **Create**.
8. In the left-hand menu, select **Branding**.
9. In the **Authorized domains** section, select **Add domain**:
   * If you're using n8n's Cloud service, add `n8n.cloud`
   * If you're [self-hosting](https://app.gitbook.com/s/jm0ZYRpZIPWge2ZSiDYO/host-n8n), add the domain of your n8n instance.
10. Select **Save** at the bottom of the page.

#### Create your Google OAuth client credentials

Next, create the OAuth client credentials in Google:

1. Access your [Google Cloud Console](https://console.cloud.google.com/). Make sure you're in the correct project.
2. In the **APIs & Services** section, select [**Credentials**](https://console.cloud.google.com/apis/credentials).
3. Select **+ Create credentials** > **OAuth client ID**.
4. In the **Application type** dropdown, select **Web application**.
5. Google automatically generates a **Name**. Update the **Name** to something you'll recognize in your console.
6.  From your n8n credential, copy the **OAuth Redirect URL**. Paste it into the **Authorized redirect URIs** in Google Console.

    
> **Note:** OAuth redirect URL for self-hosting If you're running n8n on your local machine, you don't need a public domain, SSL certificate, or port forwarding to use Google OAuth. Google allows localhost as a valid redirect URI for development purposes. Your n8n OAuth redirect URL will look something like this: http://localhost:5678/rest/oauth2-credential/callback For more details on acceptable redirect URIs, refer to Google's redirect URI documentation .

7. Select **Create**.

#### Finish your n8n credential

With the Google project and credentials fully configured, finish the n8n credential:

1. From Google's **OAuth client created** modal, copy the **Client ID**. Enter this in your n8n credential.
2. From the same Google modal, copy the **Client Secret**. Enter this in your n8n credential.
3. In n8n, select **Sign in with Google** to complete your Google authentication.
4. **Save** your new credentials.

### Video

[Embedded content](https://www.youtube.com/embed/FBGtpWMTppw)

### Troubleshooting

#### Google hasn't verified this app

#### Google Cloud app becoming unauthorized

#### redirect\_uri\_mismatch

This error means the redirect URI n8n is sending doesn't match any of the URIs registered in your Google Cloud Console OAuth client.

**Fix:** Copy the **OAuth Redirect URL** from your n8n credential panel and paste it exactly — including the protocol (`http` or `https`) and port number — into the **Authorized redirect URIs** field of your Google OAuth client.

#### Access denied / "app not verified"

This usually happens when your app is still in Testing mode and you haven't added the Google account you're trying to authenticate with as a test user.

**Fix:** Go to **APIs & Services** > **OAuth consent screen** > **Test users** and add the account you're trying to use.

#### invalid\_client

This error typically means the Client ID or Client Secret in your n8n credential doesn't match what's in Google Cloud Console.

**Fix:** Go back to your OAuth client in Google Cloud Console, copy both values fresh, and re-enter them in n8n. Watch out for accidental spaces when copying.

---

## Google Service Account

## Google Service Account

Using service accounts is more complex than OAuth2. Before you begin:

* Check if your node is [compatible](https://docs.n8n.io/integrations/builtin/credentials/google#compatible-nodes) with Service Account.
* Make sure you need to use Service Account. For most use cases, [OAuth2](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service) is a better option.
* Read the Google documentation on [Creating and managing service accounts](https://cloud.google.com/iam/docs/creating-managing-service-accounts).

### Prerequisites

* Create a [Google Cloud](https://cloud.google.com/) account.

### Set up Service Account

There are four steps to connecting your n8n credential to a Google Service Account:

1. [Create a Google Cloud Console project](https://docs.n8n.io/integrations/builtin/credentials/google/service-account#create-a-google-cloud-console-project).
2. [Enable APIs](https://docs.n8n.io/integrations/builtin/credentials/google/service-account#enable-apis).
3. [Set up Google Cloud Service Account](https://docs.n8n.io/integrations/builtin/credentials/google/service-account#set-up-google-cloud-service-account).
4. [Finish your n8n credential](https://docs.n8n.io/integrations/builtin/credentials/google/service-account#finish-your-n8n-credential).

#### Create a Google Cloud Console project

First, create a Google Cloud Console project. If you already have a project, jump to the next section:

#### Enable APIs

With your project created, enable the APIs you'll need access to:

#### Set up Google Cloud Service Account

1.  Access your [Google Cloud Console - Library](https://console.cloud.google.com/apis/library). Make sure you're in the correct project.

    <figure><figcaption>Check the project dropdown in the Google Cloud top navigation</figcaption></figure>
2. Open the left navigation menu and go to **APIs & Services > Credentials**. Google takes you to your **Credentials** page.
3. Select **+ Create credentials > Service account**.
4. Enter a name in **Service account name** and an ID in **Service account ID**. Refer to [Creating a service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts?hl=en#creating) for more information.
5. Select **Create and continue**.
6. Based on your use-case, you may want to **Select a role** and **Grant users access to this service account** using the corresponding sections.
7. Select **Done**.
8. Select your newly created service account under the **Service Accounts** section. Open the **Keys** tab.
9. Select **Add key > Create new key**.
10. In the modal that appears, select **JSON**, then select **CREATE**. Google saves the file to your computer.

#### Finish your n8n credential

With the Google project and credentials fully configured, finish the n8n credential:

1. Open the downloaded JSON file.
2. Copy the `client_email` and enter it in your n8n credential as the **Service Account Email**.
3.  Copy the `private_key`. Don't include the surrounding `"` marks. Enter this as the **Private Key** in your n8n credential.

    
> **Warning:** Older versions of n8n If you're running an n8n version older than 0.156.0, replace all instances of \n in the JSON file with new lines.

4. **Optional**: Choose if you want to [**Impersonate a User**](https://developers.google.com/identity/protocols/oauth2/service-account#delegatingauthority) (turned on).
   1. To use this option, you must [Enable domain-wide delegation](https://docs.n8n.io/integrations/builtin/credentials/google/service-account#enable-domain-wide-delegation) for the service account as a Google Workspace super admin.
   2. Enter the **Email** of the user you want to impersonate.
5. If you plan to use this credential with the [HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest) node, turn on **Set up for use in HTTP Request node**.
   1. With this setting turned on, you'll need to add **Scope(s)** for the node. n8n prepopulates some scopes. Refer to [OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes) for more information.
6. **Save** your credentials.

### Video

[Embedded content](https://www.youtube.com/embed/FzQzGODb5Gk?si=YR9vDaTet8vsj-y2)

### Troubleshooting

#### Service Account can't access Google Drive files

> **No access to my drive:**
> Google no longer allows Service Accounts created after April 15, 2025 to access `my drive`. Service Accounts now only have access to shared drives.
> While not recommended, if you need to use a Service Account to access `my drive`, you can do so by [enabling domain-wide delegation](https://docs.n8n.io/integrations/builtin/credentials/google/service-account#enable-domain-wide-delegation). You can learn more in [this post in the community](https://community.n8n.io/t/please-please-help-upload-file-google-drive-node-with-service-account-not-working/147750/15).

A Service Account can't access Google Drive files and folders that weren't shared with its associated user email.

1. Access your [Google Cloud Console](https://console.cloud.google.com) and copy your Service Account email.
2. Access your [Google Drive](https://drive.google.com) and go to the designated file or folder.
3. Right-click on the file or folder and select **Share**.
4. Paste your Service Account email into **Add People and groups**.
5. Select **Editor** for read-write access or **Viewer** for read-only access.

#### Enable domain-wide delegation

To impersonate a user with a service account, you must enable domain-wide delegation for the service account.

> **Not recommended:**
> Google recommends you [avoid using domain-wide delegation](https://cloud.google.com/iam/docs/best-practices-service-accounts#domain-wide-delegation), as it allows impersonation of any user (including super admins) and can pose a security risk.

To delegate domain-wide authority to a service account, you must be a super administrator for the Google Workspace domain. Then:

1. From your Google Workspace domain's [Admin console](https://admin.google.com/), select the hamburger menu, then select **Security > Access and data control > API Controls**.
2. In the **Domain wide delegation** pane, select **Manage Domain Wide Delegation**.
3. Select **Add new**.
4. In the **Client ID** field, enter the service account's **Client ID**. To get the Client ID:
   * Open your Google Cloud Console project, then open the [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts) page.
   * Copy the **OAuth 2 Client ID** and use this as the **Client ID** for the **Domain Wide Delegation**.
5. In the **OAuth scopes** field, enter a list of comma-separate scopes to grant your application access. For example, if your application needs domain-wide full access to the Google Drive API and the Google Calendar API, enter: `https://www.googleapis.com/auth/drive, https://www.googleapis.com/auth/calendar`.
6. Select **Authorize**.

It can take from 5 minutes up to 24 hours before you can impersonate all users in your Workspace.
