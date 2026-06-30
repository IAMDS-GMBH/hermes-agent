# Microsoft Outlook Messaging — Setup Guide

This guide explains how to connect Hermes to Microsoft Outlook via the Microsoft Graph API using **device flow authentication** (delegated permissions). Once configured, you can interact with Outlook directly from the Hermes chat — reading mail, sending messages, and working with your calendar.

---

## Overview

| Who does this step | What |
|---|---|
| App developer / IT admin | Register the Azure AD app and configure permissions |
| Azure AD admin | Grant admin consent |
| Azure AD admin | Enable device flow for the app (or per user) |
| App developer / IT admin | Share Tenant ID + Client ID with Hermes users |
| Hermes user | Enter Tenant ID + Client ID in the Outlook messaging section |
| Hermes user | Authenticate via chat command or the **Test** button |

---

## Step 1 — Register an Azure AD Application

1. Go to the [Azure portal](https://portal.azure.com) → **Azure Active Directory** → **App registrations** → **New registration**.
2. Give the app a name (e.g. `Hermes Agent`).
3. Set **Supported account types** to **Accounts in this organizational directory only** (single tenant) — or multi-tenant if needed.
4. Leave **Redirect URI** blank for now (device flow does not require one).
5. Click **Register**.

After registration, note down:
- **Application (client) ID** — shown on the app overview page.
- **Directory (tenant) ID** — also on the app overview page.

---

## Step 2 — Add Required API Permissions

In your app registration, go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**.

Add the following permissions:

| Permission | Purpose |
|---|---|
| `Mail.Read` | Read emails from the mailbox |
| `Mail.Send` | Send emails on behalf of the user |
| `Calendar.Read` | Read calendar events |
| `Calendar.ReadBasic` | Read basic calendar metadata |
| `Calendar.ReadWrite` | Create and update calendar events |
| `offline_access` | Maintain access (refresh tokens) without re-authentication |
| `User.Read` | Read the signed-in user's profile |

> **Note:** Do **not** add application permissions (app-only). All of the above must be added as **Delegated** permissions.

---

## Step 3 — Grant Admin Consent

An Azure AD administrator must grant consent for these permissions so users do not need to approve each one individually.

In **API permissions**, click **Grant admin consent for \<your tenant\>** and confirm.

The status column should show **Granted for \<your tenant\>** (green checkmark) for each permission.

---

## Step 4 — Enable Device Flow Authentication

Device flow is an OAuth 2.0 flow that lets users authenticate on a separate device or browser window using a short code. It must be explicitly allowed by Azure AD.

### Option A — Enable for the entire tenant (recommended for internal tools)

1. Go to **Azure Active Directory** → **Enterprise applications** → find your registered app.
2. Under **Properties**, ensure **User assignment required** is configured as appropriate for your org.
3. Go to **Azure Active Directory** → **Authentication methods** or check your [Conditional Access](https://portal.azure.com/#view/Microsoft_AAD_IAM/ConditionalAccessBlade) policies to confirm device code flow is not blocked.
4. In your **App registration** → **Authentication**, enable **Allow public client flows** (under **Advanced settings**). Set **Enable the following mobile and desktop flows** to **Yes**.

> This is the key toggle — without it, device code requests will be rejected.

### Option B — Enable per user via Conditional Access

If your organisation restricts auth flows via Conditional Access, work with your Azure AD admin to create a policy that allows device code flow for the specific users or groups that will use Hermes.

---

## Step 5 — Share Credentials with Hermes Users

The person who registered the app must share two values with each Hermes user:

- **Tenant ID** — the Directory (tenant) ID from the app overview
- **Client ID** — the Application (client) ID from the app overview

These do **not** need to be kept secret (unlike a client secret). They identify the app registration, not any individual user.

---

## Step 6 — Configure Hermes

### Desktop app

1. Open Hermes → **Messaging** section in the left sidebar.
2. Select **Outlook** from the platform list.
3. Enter the **Tenant ID** and **Client ID** provided by your app developer/admin.
4. Click **Save changes**.

<p align="center">
  <img src="../../assets/desktop-messaging-outlook.png" alt="Outlook messaging configuration panel" width="85%">
</p>

### CLI / `.env`

Alternatively, add to your `.env` file:

```env
OUTLOOK_TENANT_ID=<your-tenant-id>
OUTLOOK_CLIENT_ID=<your-client-id>
```

---

## Step 7 — Authenticate

There are two ways to complete the device flow authentication:

### Option A — Via chat (recommended)

Once the Tenant ID and Client ID are saved, you can ask Hermes in the chat:

> *"Authenticate Outlook"* or *"Connect my Outlook account"*

Hermes will initiate the device code flow, display a short code, and provide the Microsoft login URL. Open the URL in a browser, enter the code, and sign in with your Microsoft account. Hermes will detect the successful authentication automatically.

### Option B — Via the Test button

1. In the Hermes desktop app, go to **Messaging** → **Outlook**.
2. Click the **Test** button.
3. A dialog will appear showing:
   - A **"Open Microsoft Login"** button — click it to open the auth page in your browser.
   - A short **device code** — copy it and paste it when prompted in the browser.
4. After you complete sign-in in the browser, Hermes will confirm the connection automatically.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `AADSTS7000218: The request body must contain the following parameter: 'client_assertion' or 'client_secret'` | Public client flows not enabled | Enable **Allow public client flows** in the app's Authentication settings (Step 4) |
| `AADSTS50020: User account … does not exist in tenant` | Wrong tenant ID, or user is in a different tenant | Verify the Tenant ID matches the user's Azure AD tenant |
| `AADSTS65001: The user or administrator has not consented` | Admin consent not granted | Complete Step 3 |
| Device code expires before authentication completes | Browser session too slow | Click **Test** again to start a fresh flow |
| `Mail.Send` succeeds but emails go to Junk | SPF/DKIM not set for Graph-sent mail | Contact your IT team to allowlist Graph API outbound mail |
