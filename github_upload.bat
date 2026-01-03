@echo off
REM Quick GitHub Upload Script for Windows
REM This script automates the GitHub upload process

echo 🚀 GitHub Upload Assistant for Real-Time Video Dehazing
echo ========================================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Git is not installed!
    echo Download from: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo ✅ Git is installed
echo.

REM Get GitHub username
set /p github_username="Enter your GitHub username: "

if "%github_username%"=="" (
    echo ❌ GitHub username cannot be empty!
    pause
    exit /b 1
)

echo.
echo 📦 Preparing repository...
echo.

REM Initialize Git if not already initialized
if not exist ".git" (
    echo Initializing Git repository...
    git init
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already initialized
)

REM Check git status
echo.
echo 📋 Files to be committed:
git status --short

echo.
set /p proceed="Do you want to proceed with commit? (y/n): "

if /i not "%proceed%"=="y" (
    echo ❌ Upload cancelled
    pause
    exit /b 0
)

REM Add all files
echo.
echo 📝 Adding files...
git add .

REM Create commit
echo.
set /p commit_msg="Enter commit message (or press Enter for default): "

if "%commit_msg%"=="" (
    set commit_msg=Initial commit: Real-time video dehazing with web interface and Colab GPU support
)

git commit -m "%commit_msg%"
echo ✅ Commit created

REM Add remote
echo.
echo 🔗 Connecting to GitHub...
set repo_url=https://github.com/%github_username%/Real-time-dehazing-deep-learning.git

REM Check if remote already exists
git remote | findstr "origin" >nul 2>&1
if errorlevel 1 (
    git remote add origin "%repo_url%"
) else (
    echo Remote 'origin' already exists. Updating URL...
    git remote set-url origin "%repo_url%"
)

echo ✅ Connected to: %repo_url%

REM Rename branch to main if needed
for /f "tokens=*" %%a in ('git branch --show-current') do set current_branch=%%a
if not "%current_branch%"=="main" (
    echo Renaming branch to 'main'...
    git branch -M main
)

REM Push to GitHub
echo.
echo 🚀 Pushing to GitHub...
echo You may be prompted for your GitHub credentials
echo (Use Personal Access Token, not password)
echo.

git push -u origin main
if errorlevel 1 (
    echo.
    echo ❌ Push failed!
    echo.
    echo Troubleshooting:
    echo 1. Make sure repository exists on GitHub:
    echo    → Go to https://github.com/new
    echo    → Create repo named: Real-time-dehazing-deep-learning
    echo    → Do NOT initialize with README
    echo.
    echo 2. Authentication issues?
    echo    → Use Personal Access Token instead of password
    echo    → GitHub → Settings → Developer settings → Personal access tokens
    echo.
    echo 3. Large files detected?
    echo    → Review .gitignore file
    echo    → Remove large files: git rm --cached ^<file^>
    echo.
    pause
    exit /b 1
)

echo.
echo 🎉 SUCCESS! Your project is now on GitHub!
echo.
echo 📍 Repository URL: https://github.com/%github_username%/Real-time-dehazing-deep-learning
echo.
echo ⚠️  NEXT STEPS:
echo 1. Update README_NEW.md:
echo    - Replace YOUR_USERNAME with: %github_username%
echo    - Add your name and email
echo    - Add model weights download links
echo 2. Rename README_NEW.md to README.md
echo 3. Push updates: git add . ^&^& git commit -m "Update README" ^&^& git push
echo 4. Add repository topics on GitHub
echo 5. Create your first release
echo.

pause
