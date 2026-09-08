# Clone the `production` GitHub Environment

Source environment currently used by `cvsz/zeaz-web`:

- repository: `cvsz/zeaz-web`
- environment: `production`
- deployment URL in that repository's workflow: `https://www.zeaz.dev/`

zMovie includes `scripts/copy-github-environment.sh` to reproduce the exportable environment configuration in another repository.

## What the helper copies

- wait timer;
- prevent-self-review setting;
- required reviewer user/team IDs;
- deployment branch policy mode;
- custom deployment branch policies;
- environment variables, when the authenticated token can read/write them.

## What GitHub does not allow to be copied

GitHub never returns secret values from the Actions/Environment Secrets API. The helper can list the secret names visible in the source environment, but the values must be provisioned again from the original secure source.

Do not put secret values into this repository, shell history, issues, logs, or workflow YAML.

## Copy `cvsz/zeaz-web:production` to `cvsz/zmovie:production`

From a trusted operator machine with GitHub CLI authenticated using a token that has repository Administration write access on the target and the necessary Actions Variables/Secrets metadata permissions on the source:

```bash
git clone https://github.com/cvsz/zmovie.git
cd zmovie

SOURCE_REPO=cvsz/zeaz-web \
TARGET_REPO=cvsz/zmovie \
ENVIRONMENT=production \
bash scripts/copy-github-environment.sh
```

The helper is idempotent for the environment itself and replaces target custom deployment branch policies by default so they match the source. Set `REPLACE_BRANCH_POLICIES=false` if target-specific policies must be preserved.

## Verify

```bash
gh api repos/cvsz/zmovie/environments/production | jq '{name,protection_rules,deployment_branch_policy}'
```

If the helper reports secret names, configure those values separately in the target environment using GitHub's encrypted secret mechanism or the GitHub UI. Do not attempt to export secret values from the source repository.
