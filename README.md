# Welcome, toruk-makto, to the 2026 TDI Global Hackathon!

> [!IMPORTANT]
> This README may be **changed or overwritten** by the hackathon organisers during the event.
> If you intend to create documentation, please house it in a _separate file_.

## 🚀 Quick Start

Welcome to the hackathon! Follow these steps to get set up:

1.  **Find Your SSO ID:** Your login for most tools is your personal email transformed. For example, `foo@bar.com` becomes `foo.bar.com@db-hackathon.com`. **This is your most important credential.**
2.  **Set Your Password:** [Login to Microsoft Azure](http://portal.azure.com) first. You will be prompted to set a new password and configure 2FA on your first login.
3.  **Accept GitHub Invite:** Check the personal email you registered with for an invitation to the `db-hackathon` GitHub organization and accept it.
4.  **Get Help:** If you have any issues, the fastest way to get help is to [raise an issue in the support repo](https://github.com/db-hackathon/support/issues/new/choose).

---

## Your Hackathon Environment at a Glance

| Platform          | Link                                                                                                                            | Purpose                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **GCP**           | [Console](https://www.google.com/a/db-hackathon.com/ServiceLogin?continue=https://console.cloud.google.com)                       | Cloud provider.                             |
| **Azure**         | [Portal](http://portal.azure.com)                                                                                                | Cloud provider.                      |
| **GitHub**        | [Repo](https://github.com/db-hackathon/toruk-makto)                                                                             | Your team's code repository.                                            |
| **Terraform Cloud** | [Workspace](https://app.terraform.io/app/db-hackathon-2026/workspaces/hack-team-toruk-makto)                                            | Optional Infrastructure as Code for GCP.                                |
| **OpenShift**     | [Console](https://console-openshift-console.apps.dbhackathon.swedencentral.aroapp.io/k8s/cluster/projects/toruk-makto-official) | Optional container platform for deployments.                            |
| **Microsoft Teams** | [Teams](https://teams.microsoft.com/v2/)                                                                                        | Communication and support.                                              |
| **Support Repo**  | [Issues](https://github.com/db-hackathon/support/issues/new/choose)                                                             | **Fastest way to get help.**                                            |

---

<details>
<summary><h3>Login & Access (The Details)</h3></summary>

> [!CAUTION]
> Do not attempt logins, follow links, or otherwise conduct hackathon activity **from a DB device**.
> The whole event is designed to run **off DB's corporate infrastructure**.

> [!TIP]
> If you participated in the hackathon last year with the same personal email, you may have saved your password for your SSO account. Last year's password **won't work on the initial login**; you have a new Entra account, even if the ID is the same.

#### How do I login? (Video Guide)

Please check out the detailed [video guide here](https://github.com/db-hackathon#how-do-i-login-movie_camera).

#### Your Single Sign On (SSO) ID

Most of this year's tooling is connected to a central [Identity Provider (IdP)](https://www.cloudflare.com/en-gb/learning/access-management/what-is-an-identity-provider/), **Microsoft Entra ID**.

Your ID for the IdP is **not** the personal email address that you signed up with, but rather a transformation of it.

To determine your ID, take the personal email you signed up with, replace the `@` with a `.` and add the suffix `@db-hackathon.com`.

For example, `foo@bar.com` becomes `foo.bar.com@db-hackathon.com`.

This is the email/ID you should use when prompted for SSO login.

#### Platform-Specific Login Instructions

*   **Microsoft Azure:** Start with [Microsoft Azure](http://port
al.azure.com). Use your SSO ID and the **initial password** given in your briefing. You will be prompted to change it and set up 2FA.
*   **Google Cloud Platform:** Login via the [GCP SSO link](https://www.google.com/a/db-hackathon.com/ServiceLogin?continue=https://console.cloud.google.com).
*   **GitHub:** You must accept the invitation sent to your personal email. Attempt to [login to GitHub via SSO](https://github.com/orgs/db-hackathon/sso) first, then link your personal GitHub account.
*   **Terraform Cloud:** [Login via SSO](https://app.terraform.io/sso/sign-in) and use `db-hackathon-2026` for the *Organization Name*.
*   **RedHat OpenShift:** Visit the [OpenShift Console](https://console-openshift-console.apps.dbhackathon.swedencentral.aroapp.io/k8s/cluster/projects/toruk-makto-official) and select **AAD** to log in.
*   **Microsoft Teams:** Access via the [browser](https://teams.microsoft.com/v2/) or the [desktop app](https://www.microsoft.com/en-gb/microsoft-teams/download-app).

</details>

---

<details>
<summary><h3>Platform Guides & Usage</h3></summary>

#### Google Cloud Platform :cloud:

**APIs:**
The following APIs have been activated on your project. You cannot activate others.
* agentregistry.googleapis.com
* aiplatform.googleapis.com
* apigateway.googleapis.com
* appengine.googleapis.com
* appengineflex.googleapis.com
* appenginereporting.googleapis.com
* artifactregistry.googleapis.com
* bigquery.googleapis.com
* bigqueryconnection.googleapis.com
* chat.googleapis.com
* cloudapiregistry.googleapis.com
* cloudasset.googleapis.com
* cloudbuild.googleapis.com
* clouderrorreporting.googleapis.com
* cloudfunctions.googleapis.com
* cloudscheduler.googleapis.com
* cloudsupport.googleapis.com
* composer.googleapis.com
* contactcenteraiplatform.googleapis.com
* contactcenterinsights.googleapis.com
* dataflow.googleapis.com
* dataproc.googleapis.com
* datastudio.googleapis.com
* developerconnect.googleapis.com
* dialogflow.googleapis.com
* discoveryengine.googleapis.com
* documentai.googleapis.com
* eventarc.googleapis.com
* eventarcpublishing.googleapis.com
* fcm.googleapis.com
* firebase.googleapis.com
* firebaseinstallations.googleapis.com
* firestore.googleapis.com
* iamconnectors.googleapis.com
* iap.googleapis.com
* language.googleapis.com
* logging.googleapis.com
* modelarmor.googleapis.com
* monitoring.googleapis.com
* networksecurity.googleapis.com
* networkservices.googleapis.com
* notebooks.googleapis.com
* observability.googleapis.com
* pubsub.googleapis.com
* retail.googleapis.com
* run.googleapis.com
* saasservicemgmt.googleapis.com
* secretmanager.googleapis.com
* servicemanagement.googleapis.com
* serviceusage.googleapis.com
* spanner.googleapis.com
* speech.googleapis.com
* sql-component.googleapis.com
* sqladmin.googleapis.com
* storage-api.googleapis.com
* storage-component.googleapis.com
* storage.googleapis.com
* storagetransfer.googleapis.com
* texttospeech.googleapis.com
* timeseriesinsights.googleapis.com
* translate.googleapis.com
* videointelligence.googleapis.com
* vision.googleapis.com
* workflowexecutions.googleapis.com
* workflows.googleapis.com
* workstations.googleapis.com

**Permissions:**
Every team member has the following roles at the project level:
* roles/aiplatform.admin
* roles/aiplatform.migrator
* roles/aiplatform.tensorboardWebAppUser
* roles/aiplatform.user
* roles/apigateway.admin
* roles/appengine.appAdmin
* roles/appengine.appCreator
* roles/artifactregistry.admin
* roles/bigquery.connectionAdmin
* roles/bigquery.dataOwner
* roles/bigquery.resourceViewer
* roles/bigquery.user
* roles/bigquerydatapolicy.maskedReader
* roles/browser
* roles/chat.owner
* roles/cloudasset.viewer
* roles/cloudbuild.builds.approver
* roles/cloudbuild.builds.editor
* roles/cloudbuild.connectionAdmin
* roles/cloudbuild.integrationsOwner
* roles/cloudbuild.integrationsViewer
* roles/cloudbuild.workerPoolOwner
* roles/cloudfunctions.developer
* roles/cloudscheduler.admin
* roles/cloudsql.admin
* roles/cloudsupport.techSupportEditor
* roles/cloudtranslate.editor
* roles/composer.admin
* roles/contactcenteraiplatform.admin
* roles/contactcenterinsights.editor
* roles/dataflow.developer
* roles/dataproc.editor
* roles/datastore.owner
* roles/datastudio.viewer
* roles/developerconnect.admin
* roles/developerconnect.oauthUser
* roles/dialogflow.admin
* roles/discoveryengine.editor
* roles/discoveryengine.notebookOwner
* roles/documentai.editor
* roles/errorreporting.admin
* roles/eventarc.developer
* roles/firebase.admin
* roles/iam.roleViewer
* roles/logging.admin
* roles/monitoring.editor
* roles/notebooks.admin
* roles/notebooks.legacyViewer
* roles/oauthconfig.editor
* roles/pubsub.editor
* roles/retail.admin
* roles/run.admin
* roles/secretmanager.admin
* roles/servicemanagement.quotaViewer
* roles/serviceusage.serviceUsageConsumer
* roles/spanner.admin
* roles/speech.editor
* roles/storage.admin
* roles/storagetransfer.admin
* roles/timeseriesinsights.datasetsEditor
* roles/visionai.editor
* roles/workflows.editor
* roles/workstations.admin
* roles/workstations.networkAdmin

**Service Accounts:**

Infrastructure SA (`infrastructure@hack-team-toruk-makto.iam.gserviceaccount.com` Use this for deploying resources from GitHub Actions or Terraform Cloud. It has the same permissions as a human team member.

Workload SA (`workload@hack-team-toruk-makto.iam.gserviceaccount.com`): Attach this to your compute resources (e.g., Cloud Run, Cloud Functions). It has the following roles:

* roles/aiplatform.user
* roles/artifactregistry.createOnPushWriter
* roles/bigquery.connectionUser
* roles/bigquery.dataEditor
* roles/bigquery.dataViewer
* roles/bigquery.filteredDataViewer
* roles/bigquery.jobUser
* roles/bigquery.readSessionUser
* roles/bigquerydatapolicy.maskedReader
* roles/chat.owner
* roles/cloudasset.viewer
* roles/cloudbuild.builds.builder
* roles/cloudbuild.tokenAccessor
* roles/cloudbuild.workerPoolUser
* roles/cloudfunctions.invoker
* roles/cloudsql.client
* roles/cloudsql.instanceUser
* roles/cloudtranslate.user
* roles/composer.worker
* roles/contactcenteraiplatform.viewer
* roles/contactcenterinsights.viewer
* roles/dataflow.admin
* roles/dataflow.worker
* roles/dataproc.hubAgent
* roles/dataproc.worker
* roles/datastore.user
* roles/datastudio.editor
* roles/developerconnect.oauthUser
* roles/developerconnect.user
* roles/dialogflow.client
* roles/dialogflow.reader
* roles/discoveryengine.editor
* roles/discoveryengine.notebookOwner
* roles/documentai.viewer
* roles/errorreporting.writer
* roles/eventarc.connectionPublisher
* roles/eventarc.eventReceiver
* roles/eventarc.publisher
* roles/logging.logWriter
* roles/monitoring.metricWriter
* roles/notebooks.runner
* roles/pubsub.editor
* roles/retail.editor
* roles/run.invoker
* roles/secretmanager.secretAccessor
* roles/secretmanager.secretVersionAdder
* roles/servicemanagement.quotaViewer
* roles/serviceusage.serviceUsageConsumer
* roles/spanner.databaseUser
* roles/speech.client
* roles/storage.objectUser
* roles/storagetransfer.transferAgent
* roles/storagetransfer.user
* roles/timeseriesinsights.datasetsEditor
* roles/visionai.admin
* roles/workflows.invoker

**Using Custom Service Accounts:**
The default service accounts are de-privileged. You **must** attach your Workload SA to your compute resources.
> **For detailed examples**, see the guide **[here](./GCP_SERVICE_ACCOUNTS.md)**.

**Limitations:**
*   You have a budget of **EUR ~200**. Your team lead will receive spending notifications.
*   You **cannot** create service accounts or service account keys. Use Workload Identity Federation.

#### Gemini / Vertex AI :sparkles:

Gemini models run on the Gemini Enterprise Agent Platform (the service previously called Vertex AI). Your project already has the `aiplatform.googleapis.com` API enabled and your Workload SA holds `roles/aiplatform.user`, so you can call Gemini without extra setup. There are no API keys to manage, so you authenticate the same way you would for any other GCP API.

* **From your laptop:** sign in once with `gcloud auth application-default login`, then set your quota project with `gcloud auth application-default set-quota-project hack-team-toruk-makto`. The Google client libraries find these credentials automatically.
* **From compute (Cloud Run, Cloud Functions, a VM, OpenShift):** attach your Workload SA `workload@hack-team-toruk-makto.iam.gserviceaccount.com` to the resource. Your code reads its credentials from the metadata server through Application Default Credentials, so you do not copy or store any secret.

Install the current SDK with `pip install google-genai` and point it at Vertex:

```python
from google import genai

client = genai.Client(vertexai=True, project="hack-team-toruk-makto", location="global")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Give me three ideas for a hackathon project.",
)
print(response.text)
```

The same code runs unchanged on your laptop and on your compute, because both resolve credentials through ADC. For per-service instructions on attaching the Workload SA and more examples, see **[GCP_SERVICE_ACCOUNTS.md](./GCP_SERVICE_ACCOUNTS.md)**.

#### GitHub :bookmark_tabs:

**Access:** All team members have **maintainer** access to this repository.
**GitHub Actions Variables:** A set of useful variables has been populated for you:
* vars.APP_ENGINE_DEFAULT_SA_EMAIL - The email address of the default App Engine service account.: hack-team-toruk-makto@appspot.gserviceaccount.com
* vars.APP_ENGINE_DEFAULT_SA_ID - The fully qualified name of the default App Engine service account.: projects/hack-team-toruk-makto/serviceAccounts/hack-team-toruk-makto@appspot.gserviceaccount.com
* vars.COMPUTE_DEFAULT_SA_EMAIL - The email address of the default Compute Engine service account.: 156042242219-compute@developer.gserviceaccount.com
* vars.COMPUTE_DEFAULT_SA_ID - The fully qualified name of the default Compute Engine service account.: projects/hack-team-toruk-makto/serviceAccounts/156042242219-compute@developer.gserviceaccount.com
* vars.INFRA_SA_EMAIL - The email address representation of the SA you can use to deploy infrastructure. It has the same access rights as human team members.: infrastructure@hack-team-toruk-makto.iam.gserviceaccount.com
* vars.INFRA_SA_ID - The fully qualified ID representation of the SA you can use to deploy infrastructure.: projects/hack-team-toruk-makto/serviceAccounts/infrastructure@hack-team-toruk-makto.iam.gserviceaccount.com
* vars.OPENSHIFT_NAMESPACE - The OpenShift namespace for your team: toruk-makto-official
* vars.OPENSHIFT_REGISTRY - The OpenShift internal registry URL: image-registry.openshift-image-registry.svc:5000
* vars.OPENSHIFT_SERVER - The OpenShift cluster API endpoint URL: https://api.dbhackathon.swedencentral.aroapp.io:6443
* vars.PROJECT_ID - Your team's GCP Project ID.: hack-team-toruk-makto
* vars.PROJECT_NUMBER - Your teams' GCP Project Number.: 156042242219
* vars.WORKLOAD_IDENTITY_PROVIDER - The ID of the Workload Identity provider you cah use to authenticate from GitHub Actions to your GCP project.: projects/662541806905/locations/global/workloadIdentityPools/github-2026/providers/github-2026
* vars.WORKLOAD_SA_EMAIL - The email address representation of the SA you can attach to your workloads (e.g. to a Cloud Run service). : workload@hack-team-toruk-makto.iam.gserviceaccount.com
* vars.WORKLOAD_SA_ID - The fully qualified ID representation of the SA you can attach to your workloads (e.g. to a Cloud Run service). : projects/hack-team-toruk-makto/serviceAccounts/workload@hack-team-toruk-makto.iam.gserviceaccount.com

**Limitations:**
*   The platform owns the files seeded into this repo. They may be overwritten.
*   There are organization-wide limits on Actions minutes (50,000) and storage (50GB). Please be mindful of usage.

#### Terraform Cloud :hammer:

Your workspace is VCS-driven. Pushing to the `/terraform` directory will trigger a run.
The Google provider is pre-configured to use your infrastructure SA.
A set of useful input variables has been populated for you:

* app_engine_default_sa_email - The email address of the default App Engine service account.: hack-team-toruk-makto@appspot.gserviceaccount.com
* app_engine_default_sa_id - The fully qualified name of the default App Engine service account.: projects/hack-team-toruk-makto/serviceAccounts/hack-team-toruk-makto@appspot.gserviceaccount.com
* compute_default_sa_email - The email address of the default Compute Engine service account.: 156042242219-compute@developer.gserviceaccount.com
* compute_default_sa_id - The fully qualified name of the default Compute Engine service account.: projects/hack-team-toruk-makto/serviceAccounts/156042242219-compute@developer.gserviceaccount.com
* infra_sa_email - The email address representation of the SA you can use to deploy infrastructure. It has the same access rights as human team members.: infrastructure@hack-team-toruk-makto.iam.gserviceaccount.com
* infra_sa_id - The fully qualified ID representation of the SA you can use to deploy infrastructure.: projects/hack-team-toruk-makto/serviceAccounts/infrastructure@hack-team-toruk-makto.iam.gserviceaccount.com
* openshift_namespace - The OpenShift namespace for your team: toruk-makto-official
* openshift_registry - The OpenShift internal registry URL: image-registry.openshift-image-registry.svc:5000
* openshift_server - The OpenShift cluster API endpoint URL: https://api.dbhackathon.swedencentral.aroapp.io:6443
* project_id - Your team's GCP Project ID.: hack-team-toruk-makto
* project_number - Your teams' GCP Project Number.: 156042242219
* workload_identity_provider - The ID of the Workload Identity provider you cah use to authenticate from GitHub Actions to your GCP project.: projects/662541806905/locations/global/workloadIdentityPools/github-2026/providers/github-2026
* workload_sa_email - The email address representation of the SA you can attach to your workloads (e.g. to a Cloud Run service). : workload@hack-team-toruk-makto.iam.gserviceaccount.com
* workload_sa_id - The fully qualified ID representation of the SA you can attach to your workloads (e.g. to a Cloud Run service). : projects/hack-team-toruk-makto/serviceAccounts/workload@hack-team-toruk-makto.iam.gserviceaccount.com

#### OpenShift :rocket:

*   Your team has a project and namespace named `toruk-makto-official`.
*   A **ready-to-deploy Python API example** is in the [`openshift-api/`](./openshift-api/) directory. Push to the `main` branch to deploy it.
*   See the [troubleshooting guide](./openshift-api/DEBUGGING.md) if you have issues.

</details>

---

<details>
<summary><h3>Tutorials, Examples & FAQs</h3></summary>

#### Code & Setup Tutorials

* **DB:**
    * [Participant Briefing Deck](https://storage.cloud.google.com/hackathon_shared_storage_2026/Hackathon_Participant_Briefing26.pdf?authuser=1)
*   **Google Cloud:**
    *   [Generative AI Training Resources](https://cloud.google.com/blog/topics/training-certifications/new-google-cloud-generative-ai-training-resources)
    *   [Example GCP Apps](https://github.com/db-hackathon/support/tree/main/google-examples)
*   **Microsoft / OpenAI:**
    *   [Get started with GPT](https://learn.microsoft.com/en-us/azure/ai-services/openai/chatgpt-quickstart?tabs=command-line%2Cpython-new&pivots=programming-language-studio)
    *   [Microsoft 365 Guide](https://storage.cloud.google.com/hackathon_shared_storage/HackathonUserGuideMicrosoft365.pdf)
    *   [Power BI Guide](https://storage.cloud.google.com/hackathon_shared_storage/HackathonUserGuidePowerBI.pdf)

#### FAQs

*   **How do I authenticate with GCP APIs from my code?**
    *   **Locally:** Run `gcloud auth login --update-adc`.
    *   **On GCP Compute:** Attach your Workload SA. [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) will handle the rest.
    *   **On OpenShift:** See the example in the [`openshift-api/`](./openshift-api/) directory.
*   **How do I call Gemini / Vertex AI?**
    *   Your project has the Vertex AI API enabled and your Workload SA can use it. Authenticate with ADC (as above), then use the `google-genai` SDK with `vertexai=True`. Copy-paste examples are in [GCP_SERVICE_ACCOUNTS.md](./GCP_SERVICE_ACCOUNTS.md#gemini-models-enterprise-agent-platform).
*   **How do I deploy to Cloud Run / App Engine / Cloud Functions?**
    *   There are examples in this repository! See the [`.github/workflows/`](.github/workflows/) directory for `gcloud` examples and the `terraform/` directory for Terraform examples.

</details>

---

## When the time comes :broken_heart:

It's sad to think about the end of the event, but when the time does come, you will have **two hours from the end of the closing ceremony** to export anything from GCP that you wish to retain.

After this time, we will deactivate the billing link on your project, and **all of your resources will instantly be torn down**.

Your GitHub repository will remain available until the end of the day on **24th July**. If you wish to retain its contents, please clone it before this time.
