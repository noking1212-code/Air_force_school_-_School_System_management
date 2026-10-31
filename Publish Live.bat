@echo off
setlocal
cd /d "%~dp0"

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 goto not_connected

for /f "delims=" %%B in ('git branch --show-current') do set "CURRENT_BRANCH=%%B"
if /I not "%CURRENT_BRANCH%"=="main" goto wrong_branch

git check-ignore -q .env
if errorlevel 1 goto dotenv_not_ignored

git ls-files --error-unmatch .env >nul 2>&1
if not errorlevel 1 goto dotenv_tracked

git diff --cached --quiet
if errorlevel 1 goto staged_changes

git fetch origin main
if errorlevel 1 goto fetch_failed

git merge-base --is-ancestor origin/main HEAD
if errorlevel 1 goto remote_has_changes

git config user.name >nul 2>&1
if errorlevel 1 goto identity_missing
git config user.email >nul 2>&1
if errorlevel 1 goto identity_missing

git add -A -- .
if errorlevel 1 goto stage_failed

git diff --cached --quiet
if not errorlevel 1 goto nothing_to_publish

git diff --cached --name-only | findstr /x /i /c:".env" >nul
if not errorlevel 1 goto dotenv_staged

git commit -m "Publish local site update"
if errorlevel 1 goto commit_failed

git push origin main
if errorlevel 1 goto push_failed

echo.
echo Published to GitHub. Vercel will now update the live site.
echo https://ssm-rho.vercel.app/
goto finish

:not_connected
echo This folder is not connected to GitHub.
goto finish

:wrong_branch
echo This publish button only publishes the main branch.
goto finish

:dotenv_not_ignored
echo .env is not ignored, so publishing has been stopped to protect secrets.
goto finish

:dotenv_tracked
echo .env is already tracked by Git, so publishing has been stopped to protect secrets.
goto finish

:staged_changes
echo There are already staged changes. Unstage them before using this button.
goto finish

:fetch_failed
echo Could not check GitHub. Check your internet connection and try again.
goto finish

:remote_has_changes
echo GitHub has newer changes. Sync them into this folder before publishing.
goto finish

:identity_missing
echo Git needs your author name and email configured once before it can publish.
echo Set these in GitHub Desktop or VS Code, then click this file again.
goto finish

:stage_failed
echo Git could not prepare the changed files. Nothing was published.
goto finish

:nothing_to_publish
echo There are no local changes to publish.
goto finish

:dotenv_staged
echo A .env file was detected in the publish list. Publishing has been stopped.
goto finish

:commit_failed
echo Git could not create the publish record. Nothing was sent to GitHub.
goto finish

:push_failed
echo The local publish record was created, but GitHub did not accept the push.
echo No remote files were overwritten. Open this folder in VS Code and sync the branch.

:finish
echo.
pause
