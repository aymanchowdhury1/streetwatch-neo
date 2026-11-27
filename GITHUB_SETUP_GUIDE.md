# GitHub setup guide (beginner-friendly)

## 1. Create the repository

1. Sign in to GitHub and choose **New repository**.
2. Name it `streetwatch-neo`.
3. Choose Private if you do not want the source public.
4. Do not add a README, license or .gitignore on GitHub because this project already contains them.
5. Create the empty repository.

## 2. Use GitHub Desktop (easy option)

1. Install GitHub Desktop from https://desktop.github.com/.
2. Sign in to your GitHub account.
3. Choose **File → Add Local Repository**.
4. Select the extracted `streetwatch-neo` project folder.
5. If GitHub Desktop says it is not a repository, choose **Create a Repository** and use the project folder.
6. Review the changed files. Confirm `.env`, `firmware/StreetWatchESP32/config.h`, `streetwatch.db`, `*.sqlite`, uploads, and private key files are ignored. Do not force-add them.
7. Enter a summary such as `Prepare StreetWatch Neo for Render and ESP32 AP setup`.
8. Click **Commit to main**.
9. Click **Publish repository** and choose Private/Public.

## 3. Verify secret exclusions

The `.gitignore` file excludes `.env`, the real firmware `config.h`, local databases, uploads, Python bytecode and PEM/private key files. The example templates remain included. Before publishing, inspect the GitHub Desktop Changes tab and ensure no credential files are staged.

If a real token or password was committed in the past, deleting the file in a later commit does not erase it from Git history. Revoke/rotate it and consider rewriting repository history before making the repository public.

## 4. Connect Render

1. Open Render and connect your GitHub account.
2. Choose **New → Blueprint** and select the `streetwatch-neo` repository, or create a Web Service manually.
3. Render reads `render.yaml`; review the free plan, build/start command and region.
4. Set the `INITIAL_ADMIN_PASSWORD` and `DATABASE_URL` environment variables.
5. Deploy.

## 5. Automatic deployment

`render.yaml` sets `autoDeploy: true`. When you commit and push changes to the tracked `main` branch, Render automatically builds and deploys the latest commit. Check Render's Events/Logs after each deploy.

## 6. Safe daily workflow

1. Make code changes locally.
2. Test with `python -m compileall -q .`.
3. Review GitHub Desktop's Changes tab.
4. Commit with a descriptive summary.
5. Push origin.
6. Wait for Render deploy to finish and check `/healthz`.

Never store ESP32 tokens, Wi-Fi passwords, `.env` or real `config.h` in GitHub.
