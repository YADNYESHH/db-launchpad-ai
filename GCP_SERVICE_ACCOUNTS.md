# Using Custom Service Accounts in GCP

The default compute service account in your project has been de-privileged. Whenever you provision compute (e.g., a VM, Cloud Run service, or Cloud Function), you **must** attach your Workload SA: `workload@hack-team-toruk-makto.iam.gserviceaccount.com`.

This is usually referred to in the GCP documentation as "attaching a custom SA"

Both your [GitHub Actions workflows](./.github/workflows/) and [Terraform Cloud workspace](https://app.terraform.io/app/db-hackathon-2026/workspaces/hack-team-toruk-makto) have pre-populated variables containing the Workload SA email.

Below are examples of how to attach your Workload SA to various GCP services.

---

### App Engine

*   **gcloud:** [User-managed service accounts](https://cloud.google.com/appengine/docs/legacy/standard/python/user-managed-service-accounts#gcloud)
*   **Terraform (Flex):** [`service_account` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/app_engine_flexible_app_version#service_account)
*   **Terraform (Standard):** [`service_account` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/app_engine_standard_app_version#service_account)

### Cloud Build

*   **gcloud:** [Configure user-specified service accounts](https://cloud.google.com/build/docs/securing-builds/configure-user-specified-service-accounts)
    *   Ensure you specify the `--service-account=workload@hack-team-toruk-makto.iam.gserviceaccount.com` parameter of `gcloud builds submit`.
    *   Additionally, specify the `--config=...` parameter where you set the logging option to `CLOUD_LOGGING_ONLY`.
*   **Terraform:** [`service_account_email` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudbuild_trigger#service_account_email)

### Cloud Composer

*   **Console:** [Create an environment](https://cloud.google.com/composer/docs/how-to/managing/creating#console)
*   **gcloud:** [Create an environment](https://cloud.google.com/composer/docs/how-to/managing/creating#gcloud)
*   **Terraform:** [Create an environment](https://cloud.google.com/composer/docs/how-to/managing/creating#terraform)

### Cloud Functions

*   **Console:** [Configuring function identity](https://cloud.google.com/functions/docs/securing/function-identity#console)
*   **gcloud:** [Configuring function identity](https://cloud.google.com/functions/docs/securing/function-identity#gcloud)
*   **Terraform (Gen1):** [`service_account_email` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions_function#service_account_email)
*   **Terraform (Gen2):** [`service_account_email` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions2_function#service_account_email)

### Cloud Run

*   **Console:** [Configuring service identity](https://cloud.google.com/run/docs/securing/service-identity#console)
*   **gcloud:** [Configuring service identity](https://cloud.google.com/run/docs/securing/service-identity#gcloud)
*   **Terraform:** [Configuring service identity](https://cloud.google.com/run/docs/securing/service-identity#terraform)

### Dataflow

*   **Docs:** [Specify a user-managed worker service account](https://cloud.google.com/dataflow/docs/concepts/security-and-permissions#specify_a_user-managed_worker_service_account)
*   **Terraform:** [`service_account_email` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dataflow_job#service_account_email)
*   **Terraform (Flex):** [`parameters` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dataflow_flex_template_job#parameters)

### Cloud Scheduler

*   **Docs:** [Cloud Scheduler authentication](https://cloud.google.com/scheduler/docs?gclsrc=aw.ds&gad_source=1&gad_campaignid=20376984227&gclid=CjwKCAjw4efDBhATEiwAaDBpboW0I164la0GbnEBo_PTcemx4h7bsZOwIGmz0FGEnd4jP624uUU7eRoCo18QAvD_BwE)
*   **Terraform:** [`service_account_email` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_scheduler_job#service_account_email)

### Dataproc

*   **Console:** [Service accounts in Dataproc clusters](https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/service-accounts#console)
*   **gcloud:** [gcloud command](https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/service-accounts#gcloud-command)
*   **Terraform:** [`service_account` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dataproc_cluster#service_account)

### Notebooks (Vertex AI Workbench)

*   **Console:** [Create a user-managed notebooks instance](https://cloud.google.com/vertex-ai/docs/workbench/user-managed/create-new#console) (see step 9)
*   **gcloud:** [`--service-account` flag](https://cloud.google.com/sdk/gcloud/reference/notebooks/instances/create#--service-account)
*   **Terraform:** [`service_account` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/notebooks_instance#service_account)

### Workflows

*   **Docs:** [Deploy a workflow with a custom service account](https://cloud.google.com/workflows/docs/authentication#deploy_a_workflow_with_a_custom_service_account)
*   **Terraform:** [`service_account` argument](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/workflows_workflow#service_account)

### Vertex AI (General)

*   **Docs:** [Use a custom service account](https://cloud.google.com/vertex-ai/docs/general/custom-service-account#attach)
*   **Note:** Vertex AI's Console UI does not always expose the field necessary to specify a user-managed SA. However, most such screens have a `View Code` button in the top right. The generated code is populated with the fields you entered in the UI. Using the `curl` option, you can add the missing attribute in a text editor (typically `"serviceAccount": "workload@hack-team-toruk-makto.iam.gserviceaccount.com"`) and execute the resulting command in Cloud Shell.

#### Example: Tuning a Language Model with `curl`

Here's a corrected example for tuning a language model using the `curl` command.

```shell
PROJECT_ID="hack-team-toruk-makto"

curl \
-X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json; charset=utf-8" \
https://europe-west4-aiplatform.googleapis.com/v1/projects/hack-team-toruk-makto/locations/europe-west4/pipelineJobs?pipelineJobId=tune-large-model-$(date +"%Y%m%d%H%M%S") -d \
$'{
    "displayName": "tune-large-model",
    "serviceAccount": "workload@hack-team-toruk-makto.iam.gserviceaccount.com",
    "runtimeConfig": {
        "gcsOutputDirectory": "gs://artifacts.hack-team-toruk-makto.appspot.com/Foo/",
        "parameterValues": {
            "location": "us-central1",
            "project": "hack-team-toruk-makto",
            "large_model_reference": "text-bison@001",
            "model_display_name": "mytunedmodel_1",
            "train_steps": 100,
            "encryption_spec_key_name": "",
            "dataset_uri": "gs://artifacts.hack-team-toruk-makto.appspot.com/Bar.jsonl",
            "evaluation_data_uri": "",
            "evaluation_output_root_dir": "",
            "learning_rate": 3
        }
    },
    "templateUri": "https://us-kfp.pkg.dev/ml-pipeline/large-language-model-pipelines/tune-large-model/v2.0.0"
}'
```

### Gemini Models (Enterprise Agent Platform)

Gemini runs on the Enterprise Agent Platform, the service formerly called Vertex AI. The `aiplatform.googleapis.com` API is enabled on your project and your Workload SA (`workload@hack-team-toruk-makto.iam.gserviceaccount.com`) has `roles/aiplatform.user`, which is enough to send prompts to Gemini. Because you cannot create service account keys, authenticate through Application Default Credentials (ADC) in both cases below.

**From your local desktop (gcloud ADC)**

Sign in once so the client libraries can find your user credentials:

```shell
gcloud auth application-default login
gcloud auth application-default set-quota-project hack-team-toruk-makto
```

**From a compute workload (Workload SA + client library)**

Attach your Workload SA to the resource that runs your code (see the Cloud Run, Cloud Functions, Dataflow and other sections above). At runtime the Google client libraries read the SA's credentials from the metadata server through ADC. You never copy a secret into the container or VM.

**Calling Gemini (Python, `google-genai`)**

The Google Gen AI SDK is the current client library and runs with the same code locally and on compute:

```shell
pip install google-genai
```

```python
from google import genai

# vertexai=True routes the SDK to the Enterprise Agent Platform (Vertex),
# so it uses your ADC credentials and your project's quota.
client = genai.Client(
    vertexai=True,
    project="hack-team-toruk-makto",
    location="global",  # or a region, e.g. europe-west1
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Summarise the text below in two bullet points.",
)
print(response.text)
```

You can supply the same settings through environment variables instead of arguments, which suits containers:

```shell
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="hack-team-toruk-makto"
export GOOGLE_CLOUD_LOCATION="global"
```

```python
from google import genai

client = genai.Client()  # reads the variables above
```

Notes:

* `location` can be `global` (broadest model availability) or a specific region such as `europe-west1`, the default region for your environment. Choose a region if you have data-locality requirements.
* Model IDs change over time. If `gemini-2.5-flash` is unavailable, list the current models in the [Model Garden](https://console.cloud.google.com/vertex-ai/model-garden) or the [Gemini model docs](https://cloud.google.com/vertex-ai/generative-ai/docs/models).
* For raw HTTP, the `curl` pattern from the tuning example above works against any Enterprise Agent Platform endpoint: `Authorization: Bearer $(gcloud auth print-access-token)`.