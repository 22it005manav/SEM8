# 🚀 GitHub Upload Guide

Complete step-by-step instructions for uploading your Real-Time Video Dehazing project to GitHub.

---

## 📋 Prerequisites

Before you begin:

✅ **Git installed** - Download from https://git-scm.com/downloads  
✅ **GitHub account** - Sign up at https://github.com  
✅ **Model weights prepared** - Either exclude (recommended) or use Git LFS  
✅ **Project cleaned** - Remove unnecessary files

---

## 🎯 Quick Upload (5 Steps)

### Step 1: Create GitHub Repository

1. Go to https://github.com
2. Click **"New"** (green button, top-right)
3. Fill in repository details:
   - **Name:** `Real-time-dehazing-deep-learning`
   - **Description:** `Production-ready deep learning system for real-time video dehazing with web interface and Google Colab GPU support`
   - **Visibility:** Public (or Private)
   - **✓ Do NOT** initialize with README (we already have one)
4. Click **"Create repository"**

### Step 2: Initialize Local Git Repository

Open terminal in your project directory:

```bash
cd "d:\8 SEM VIDEO PROJECT\Real-time-dehazing-deep-learning"
```

Initialize Git:

```bash
git init
```

### Step 3: Add Files to Git

**IMPORTANT:** Review `.gitignore` to ensure large files are excluded!

```bash
# Check which files will be added (review this list!)
git status

# Add all files (respects .gitignore)
git add .

# Create first commit
git commit -m "Initial commit: Real-time video dehazing with web interface and Colab GPU support"
```

### Step 4: Connect to GitHub

Replace `YOUR_USERNAME` with your GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/Real-time-dehazing-deep-learning.git
```

Or use SSH (if you have SSH keys set up):

```bash
git remote add origin git@github.com:YOUR_USERNAME/Real-time-dehazing-deep-learning.git
```

### Step 5: Push to GitHub

```bash
# Push to main branch
git push -u origin main
```

If you encounter "master" branch instead of "main":

```bash
git branch -M main
git push -u origin main
```

🎉 **Done!** Your repository is now live at `https://github.com/YOUR_USERNAME/Real-time-dehazing-deep-learning`

---

## 📦 Handling Large Files (Model Weights)

Your model weights (\*.pth files) are **automatically excluded** by `.gitignore`. You have two options:

### Option A: Host Weights Separately (Recommended ✓)

**1. Upload to Google Drive:**

1. Create a folder: "DeepDehazeNet-Pretrained-Models"
2. Upload your model files:
   - `dehazenet_8layers_best.pth`
   - `dehazenet_16layers_best.pth`
3. Set sharing to "Anyone with the link can view"
4. Get shareable link

**2. Update README:**

Replace `YOUR_DRIVE_LINK` in `README_NEW.md` with your Google Drive folder link.

**3. Add download instructions:**

Create [MODELS_DOWNLOAD.md](MODELS_DOWNLOAD.md):

````markdown
# 📥 Model Weights Download

Download pre-trained model weights and place them in `models/pretrained/`:

## Direct Download Links

- **8-Layer Model (Recommended):** [Download](https://drive.google.com/YOUR_FILE_ID)
- **16-Layer Model (Premium):** [Download](https://drive.google.com/YOUR_FILE_ID)

## Installation

1. Download both `.pth` files
2. Place them in: `models/pretrained/`
3. Verify:
   ```bash
   ls models/pretrained/
   # Should show: dehazenet_8layers_best.pth, dehazenet_16layers_best.pth
   ```
````

````

### Option B: Use Git LFS (Advanced)

If you want to include weights in the repository:

**1. Install Git LFS:**

```bash
git lfs install
````

**2. Track model files:**

```bash
git lfs track "*.pth"
git add .gitattributes
```

**3. Add and commit:**

```bash
git add models/pretrained/*.pth
git commit -m "Add pre-trained model weights via Git LFS"
git push
```

**⚠️ Warning:** GitHub LFS has bandwidth limits (1GB/month free).

---

## ✅ Pre-Upload Checklist

Before pushing, verify:

- [ ] `.gitignore` properly excludes large files
- [ ] `README_NEW.md` renamed to `README.md`
- [ ] Update your name/email in README
- [ ] Update GitHub username in URLs
- [ ] Remove sensitive information (API keys, passwords)
- [ ] Test locally: `python app.py` works
- [ ] Check file sizes: `git ls-files | xargs du -h | sort -h`
- [ ] Create `.gitkeep` files for empty directories

---

## 🔄 Updating Your Repository

After initial upload, make changes and push updates:

```bash
# 1. Make your changes to files

# 2. Check what changed
git status

# 3. Add changes
git add .

# 4. Commit with descriptive message
git commit -m "Fix: Updated model loading fallback mechanism"

# 5. Push to GitHub
git push
```

---

## 🌿 Creating Branches (Optional)

For feature development:

```bash
# Create and switch to new branch
git checkout -b feature/new-model-architecture

# Make changes and commit
git add .
git commit -m "Add: Implemented 32-layer model variant"

# Push branch to GitHub
git push -u origin feature/new-model-architecture
```

Then create Pull Request on GitHub to merge into main.

---

## 📝 Writing Good Commit Messages

Follow these conventions:

```bash
# Format: <type>: <description>

# Types:
git commit -m "Add: New feature X"           # New feature
git commit -m "Fix: Resolved bug in Y"       # Bug fix
git commit -m "Update: Improved Z performance" # Enhancement
git commit -m "Docs: Updated README"         # Documentation
git commit -m "Refactor: Cleaned up code"    # Code restructuring
git commit -m "Test: Added unit tests"       # Testing
```

**Examples:**

```bash
git commit -m "Add: Google Colab GPU support with ngrok tunneling"
git commit -m "Fix: Model loading fallback for missing 4-layer weights"
git commit -m "Update: Enhanced web UI with side-by-side comparison"
git commit -m "Docs: Added comprehensive Colab setup guide"
```

---

## 🚨 Troubleshooting

### Problem: "Large files detected"

**Solution:** Files over 100MB rejected by GitHub.

```bash
# Remove file from staging
git reset HEAD path/to/large/file.pth

# Add to .gitignore
echo "path/to/large/file.pth" >> .gitignore

# Commit without large file
git commit -m "Remove large files from tracking"
```

### Problem: "Authentication failed"

**Solution 1:** Use Personal Access Token (not password)

1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`
4. Use token as password when pushing

**Solution 2:** Set up SSH keys

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
```

### Problem: "Files already tracked by Git"

**Solution:** Remove from Git cache (keeps local file):

```bash
# Remove specific file
git rm --cached uploads/large_video.mp4

# Remove directory
git rm -r --cached outputs/

# Commit the removal
git commit -m "Remove tracked files now in .gitignore"
```

### Problem: "Merge conflicts"

**Solution:** Pull changes first:

```bash
git pull origin main --rebase
# Resolve conflicts in editor
git add .
git rebase --continue
git push
```

---

## 🎨 Enhancing Your Repository

### Add LICENSE

Create [LICENSE](LICENSE) file:

```bash
# MIT License recommended for open source
curl https://raw.githubusercontent.com/licenses/license-templates/master/templates/mit.txt > LICENSE
```

Edit and add your name/year.

### Add CONTRIBUTING.md

Create guidelines for contributors:

```markdown
# Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Write tests
5. Submit pull request

## Code Style

- Use Black formatter
- Follow PEP 8
- Add docstrings
```

### Add GitHub Actions (Optional)

Create `.github/workflows/test.yml` for automatic testing:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.9"
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/
```

---

## 📊 Repository Analytics

After upload, enable:

1. **GitHub Insights** - Track stars, forks, traffic
2. **Dependency Graph** - Security alerts
3. **GitHub Pages** - Host documentation (optional)
4. **Releases** - Create versioned releases

---

## 🔗 Next Steps After Upload

1. **Update Links:**

   - Replace `YOUR_USERNAME` in README with your GitHub username
   - Update all repository URLs
   - Add model weights download links

2. **Add Repository Topics:**

   - Go to repository → About → Settings (gear icon)
   - Add topics: `deep-learning`, `pytorch`, `computer-vision`, `video-dehazing`, `fastapi`, `react`, `google-colab`

3. **Create Release:**

   - Go to Releases → Draft a new release
   - Tag: `v1.0.0`
   - Title: "Initial Release - Real-time Video Dehazing"
   - Description: Feature list and setup instructions

4. **Share Your Work:**
   - Post on r/MachineLearning, r/computervision
   - Share on LinkedIn/Twitter
   - Add to your portfolio

---

## 📧 Support

**Questions?** Open an issue on GitHub or contact maintainers.

**Found a bug?** Create an issue with:

- Description of problem
- Steps to reproduce
- Expected vs. actual behavior
- System information

---

## ✅ Upload Verification

After pushing, verify on GitHub:

- [ ] All files uploaded correctly
- [ ] README displays properly
- [ ] .gitignore working (large files not uploaded)
- [ ] Repository description set
- [ ] License file present
- [ ] Topics/tags added
- [ ] Links in README work
- [ ] Images/badges display

---

**🎉 Congratulations! Your project is now public on GitHub!**

Star your own repository and share it with the world! 🌟
