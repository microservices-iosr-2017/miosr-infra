
## GCP Setup

### Configure GC Image Repository
Goal: automatic building of docker images - but not for all commits, only for
ones specifically marked for building. GC Image Builder is going to watch our
GitHub repository for tags matching \[prod|stag\]-.+ regex.

\
Sidenotes:
* GC Image Builder doesn't watch GitHub repostiroy directly, but mirrors it first to
GC Source Repository, and then watches that repository
* This setup plays nicely with GitHub releases feature (if we use tags for that
purpose)

\
Steps:
1. Go to GC Image Repository and enable it.
1. Create new _Build trigger_
![Build trigger configuration](md_images/build-trigger-setup.png)

Done - creating new release should automatically cause GC Image Repository to initiate
build.

We have to repeat this process for each repository we want to have dockerized.

### Configure GitHub
Tag-based setup described previously doesn't really require any special organization
from GitHub. However, to keep things clean additional _release_ branch could be
introduced, and only stuff from this branch is released (at least using _prod_ tags).
This feature should come in especially handy when working with _stage_ releases,
which can be based on any commit on any branch.
When branch is merged to release, I would strongly recommend considering _squash-merge_
strategy.

Versioning convention:
* production release: X.X.0
* staging releases: X.X.Y - X.X is production release on which it's based, Y is
incremented every time new staging release is made

### Creating cluster

Preqreuisties:
* install gcloud
* run `gcloud init`, set default project id and zone (currently _europe-west3-a_)
* install kubectl \
`gcloud components install kubectl`

Then use the following command to create cluster:
```
gcloud container clusters create miosr --num-nodes=3
```
And get cluster credentials for `kubectl`:
```
gcloud container clusters get-credentials miosr --zone europe-west3-a
```

### Deplying services

```
python upsert_resources.py -s crud|users|frontend
```

_Warning_
Script doesn't restart deployment when configuration changes - you have to
do it manually.

### Setting up API gateway

After creating cluster and delpying `crud` and `users` services:
1. Open `openapi.yaml` file and configure domain name for the service.
Both `host` and `x-google-endpoints/name` parameters should be set to:
`"[API_NAME].endpoints.[PROJECT_ID].cloud.goog"`, where
    * `[PROJECT_ID]` should be substituted with the current project id,
    * `[API_NAME]` is free to choose.
2. Set up the API endpoint:
    ```
    gcloud endpoints services deploy openapi.yaml
    ```
3. Inside `nginx/vars.json` file set the `endpoint_name` and `endpoint_version` according to the output of the command:
    ```
    gcloud endpoints configs list --service=[API_NAME].endpoints.[PROJECT_ID].cloud.goog
    ```
4. Deploy the `nginx` service:
    ```
    python upsert_resources.py -s nginx -i nginx.conf
    ```
5. Once again open the `openapi.yaml` file and set the `x-google-endpoints/target` parameter to the `EXTERNAL-IP` of the `nginx` service, which can be obtained from:
    ```
    kubectl get service nginx-service
    ```
6. Update the API endpoint:
    ```
    gcloud endpoints services deploy openapi.yaml
    ```
7. In the [console](https://console.cloud.google.com/apis/credentials?_ga=2.45599268.1624186116.1516013623-288541820.1516012998) generate API key:
    * Click Create credentials, then select API key.

8. Now the API is ready to use. Try to register in the system:
    ```
    curl -i -X POST -H "Content-Type:application/json" \
         -d '{"username":"my-name","password":"my-pass"}' \
         http://[API_NAME].endpoints.[PROJECT_ID].cloud.goog:9692/auth/register?key=[API_KEY]
    ```
