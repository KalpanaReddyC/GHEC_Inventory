# GitHub Enterprise Inventory - Quick Start Guide

Get up and running in **15 minutes** with this streamlined setup guide.

> **Need More Details?** See [README.md](README.md) for comprehensive documentation including troubleshooting, API endpoints, and security best practices.

## Choose Your Execution Method

This tool can be run in two ways:

### 🤖 **Option A: GitHub Actions Workflow** (Recommended)
- ✅ No local setup required
- ✅ Runs automatically in the cloud
- ✅ Artifacts stored for 90 days
- ✅ Best for scheduled/recurring inventories
- ⏱️ **Setup time: 5 minutes**

### 💻 **Option B: Local Script Execution**
- ✅ Full control over execution
- ✅ Immediate results
- ✅ Best for one-time inventories or testing
- ⏱️ **Setup time: 15 minutes**

---

## Option A: GitHub Actions Workflow Setup (5 minutes)

### Prerequisites
- GitHub Enterprise account with admin access
- Repository with Actions enabled
- 5 minutes of your time

### Step 1: Fork or Clone This Repository (1 minute)
1. Fork this repository to your GitHub account, or
2. Create a new repository and copy these files

### Step 2: Create GitHub Token (3 minutes)
1. Go to: **GitHub.com** → Your **Profile Picture** → **Settings**
2. Scroll to: **Developer settings** (bottom left)
3. Click: **Personal access tokens** → **Tokens (classic)**
4. Click: **"Generate new token (classic)"**
5. Name it: `Enterprise Inventory Tool`
6. Set expiration: **90 days**
7. **Select these scopes** (check the boxes):
   - ✅ **repo** (all sub-items)
   - ✅ **admin:org** (all sub-items) - **CRITICAL for runners**
   - ✅ **admin:enterprise**
8. Click **"Generate token"**
9. **Copy the token** (starts with `ghp_`) - you won't see it again!

**Optional**: Create 2-3 more tokens with the same scopes for better performance. Separate with commas in Step 3.

### Step 3: Configure Repository Secrets (1 minute)
1. In your repository, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** and add:
   - **Name**: `ENTERPRISE_NAME`
   - **Value**: Your enterprise name (e.g., `my-company`)
3. Click **"New repository secret"** again and add:
   - **Name**: `Secret_tokens`
   - **Value**: Your PAT(s) from Step 2 (comma-separated if multiple)

**Optional - Testing Mode**:
4. Go to **Variables** tab → Click **"New repository variable"**:
   - **Name**: `MAX_ORGS_TO_PROCESS`
   - **Value**: `1` (to test with just 1 org)
   - Remove this variable for full inventory run

### Step 4: Run the Workflow (1 minute)
1. Go to **Actions** tab in your repository
2. Click **"GitHub Enterprise Inventory Collection"** workflow
3. Click **"Run workflow"** button
4. Select branch (usually `main`)
5. Click **"Run workflow"**

### Step 5: Download Results
1. Wait for workflow to complete (5-60 minutes depending on size)
2. Click on the completed workflow run
3. Scroll to **Artifacts** section at the bottom
4. Download:
   - `github-inventory-repositories-XXX` (repository data)
   - `github-inventory-organizations-XXX` (organization data)
   - `inventory-logs-XXX` (execution logs)

**✅ Done!** Extract the ZIP files to access your CSV reports.

---

## Option B: Local Script Execution Setup (15 minutes)

### Prerequisites
- GitHub Enterprise account with admin access
- Python 3.8+ installed
- 15 minutes of your time
- Internet connection

## 5-Step Local Setup

### Step 1: Install Python (5 minutes)

#### Windows
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ **Check "Add Python to PATH"**
4. Click "Install Now"
5. Verify: Open Command Prompt and run:
   ```cmd
   python --version
   ```

#### macOS
```bash
brew install python@3.12
python3 --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.12 python3-pip
python3 --version
```

---

### Step 2: Download & Setup Project (2 minutes)

1. **Extract the project files** to a folder
2. **Open terminal/command prompt** in that folder
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

### Step 3: Create GitHub Token (3 minutes)

1. Go to: **GitHub.com** → Your **Profile Picture** → **Settings**
2. Scroll to: **Developer settings** (bottom left)
3. Click: **Personal access tokens** → **Tokens (classic)**
4. Click: **"Generate new token (classic)"**
5. Name it: `Enterprise Inventory Tool`
6. Set expiration: **90 days**
7. **Select these scopes** (check the boxes):
   - ✅ **repo** (all sub-items)
   - ✅ **admin:org** (all sub-items) - **CRITICAL for runners**
   - ✅ **admin:enterprise**
8. Click **"Generate token"**
9. **Copy the token** (starts with `ghp_`) - you won't see it again!

**Optional but recommended**: Create 2-3 more tokens with the same scopes for better performance.

---

### Step 4: Configure Settings (3 minutes)

1. **Copy the example configuration**:
   ```bash
   # Windows (Command Prompt)
   copy .env.example .env
   
   # Windows (PowerShell)
   Copy-Item .env.example .env
   
   # macOS/Linux
   cp .env.example .env
   ```

2. **Edit `.env` file** (use Notepad, VS Code, or any text editor):
   ```env
   # 1. Your enterprise name
   GITHUB_ENTERPRISE_NAME=my-company
   
   # 2. Your token(s) - comma-separated if multiple
   GITHUB_PATS=ghp_yourTokenHere
   
   # 3. Keep these as-is
   GITHUB_API_URL=https://api.github.com
   GITHUB_GRAPHQL_URL=https://api.github.com/graphql
   REPO_CSV_FILE=github_inventory_repositories.csv
   ORG_CSV_FILE=github_inventory_organizations.csv
   
   # 4. Optional: Test with 1 org first
   MAX_ORGS_TO_PROCESS=1
   ```

3. **Save the file**

---

### Step 5: Run the Tool (2 minutes)

```bash
python github_inventory.py
```

**What happens:**
- ✅ Connects to GitHub Enterprise
- ✅ Collects organization and repository data
- ✅ Saves CSV files to `output/` folder
- ✅ Saves execution log to `output/logs/`

**When complete, you'll have:**
- `output/github_inventory_repositories.csv` - Detailed repo data (24 columns)
- `output/github_inventory_organizations.csv` - Org summary (15 columns)
- `output/logs/inventory_*.log` - Execution log

---

## Comparison: Workflow vs Local Execution

| Feature | GitHub Actions Workflow | Local Script |
|---------|------------------------|--------------|
| **Setup Time** | 5 minutes | 15 minutes |
| **Python Installation** | Not required | Required |
| **Execution Location** | GitHub's cloud | Your computer |
| **Results Storage** | Artifacts (90 days) | Local files |
| **Scheduling** | Easy (cron syntax) | Manual or cron jobs |
| **Best For** | Recurring inventories | One-time runs, testing |
| **Network Requirements** | None on your end | Stable internet |
| **Cost** | Free (GitHub Actions minutes) | Free |

---

## Output Files (Both Methods)

### Repository CSV (24 columns)
Key data: Org, Repo name, Visibility, Size, Language, Workflows, Branches, Tags, Runners, Webhooks, Forks, Stars, etc.

### Organization CSV (15 columns)
Key data: Org name, Total repos, Total teams, Webhooks, Apps, Self-hosted runners, GitHub-hosted runners, etc.

---

## Quick Troubleshooting

### For Both Methods
| Problem | Solution |
|---------|----------|
| **Runners show 0** but exist | Edit token in GitHub → Add `admin:org` scope → Update token/secret |
| **"No organizations found"** | Add `admin:enterprise` scope to token |
| **Rate limit errors** | Create more tokens, add comma-separated to `.env` or Secret_tokens |

### GitHub Actions Workflow
| Problem | Solution |
|---------|----------|
| **Workflow not appearing** | Ensure `.github/workflows/github-inventory.yml` exists in repository |
| **"Secret not found" error** | Check Settings → Secrets → Verify `ENTERPRISE_NAME` and `Secret_tokens` exist |
| **No artifacts generated** | Check workflow logs for errors; verify secrets are correct |
| **Workflow taking too long** | Normal for large enterprises (30-60 min); check in-progress logs |

### Local Execution
| Problem | Solution |
|---------|----------|
| **"ModuleNotFoundError"** | Run `pip install -r requirements.txt` |
| **Script hangs** | Large enterprise? Can take 30-60 min. Check `output/logs/*.log` |
| **".env file not found"** | Copy `.env.example` to `.env` and configure |

---

## Testing Mode

### GitHub Actions Workflow
1. Go to repository **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Create variable: `MAX_ORGS_TO_PROCESS` = `1`
3. Run workflow
4. Verify output looks correct
5. Delete the variable for full run

### Local Script
To test with just 1 organization before running full inventory:

1. Edit `.env` file
2. Set: `MAX_ORGS_TO_PROCESS=1`
3. Run: `python github_inventory.py`
4. Verify output looks correct
5. Set `MAX_ORGS_TO_PROCESS=0` (or remove line) for full run

---

## Scheduling (GitHub Actions Only)

To run the inventory automatically on a schedule:

1. Edit `.github/workflows/github-inventory.yml`
2. Add schedule trigger under `on:`:
   ```yaml
   on:
     workflow_dispatch:  # Keep manual trigger
     schedule:
       - cron: '0 2 * * 1'  # Every Monday at 2 AM UTC
   ```
3. Commit and push the change

Common schedule examples:
- Daily: `'0 2 * * *'`
- Weekly: `'0 2 * * 1'` (Monday)
- Monthly: `'0 2 1 * *'` (1st of month)

---

## Important Notes

### Runner Data Requires `admin:org` Scope
- Self-hosted runners: `Org_Runners_SelfHosted`, `Repo_Runners`
- GitHub-hosted runners: `Org_Runners_GitHubHosted`
- Without `admin:org`, all runner counts will be **0**

### Security (Both Methods)

**Local Script:**
- ✅ Never commit `.env` file (already in `.gitignore`)
- ✅ Store tokens securely
- ✅ Rotate tokens every 90 days
- ❌ Don't share tokens via email/chat

**GitHub Actions:**
- ✅ Always use repository secrets (never hardcode tokens)
- ✅ Secrets are encrypted and never exposed in logs
- ✅ Rotate tokens every 90 days and update secrets
- ✅ Limit repository access to trusted collaborators

### Performance (Both Methods)
- **Small** (< 100 repos): 5-10 minutes
- **Medium** (100-500 repos): 15-30 minutes
- **Large** (500+ repos): 30-60+ minutes
- Use multiple tokens for 5x faster execution

---

## Next Steps

✅ **You're done!** 

**GitHub Actions:** Download artifacts from the workflow run.  
**Local Script:** Check the `output/` folder for CSV files.

📖 **Need more details?**
- Full documentation: [README.md](README.md)
- Workflow file: [.github/workflows/github-inventory.yml](.github/workflows/github-inventory.yml)
- Troubleshooting guide: See "Troubleshooting" section in README.md
- PAT scope reference: See "GitHub Personal Access Token (PAT) Setup" in README.md

---

**Version**: 2.0 | **Last Updated**: January 2026 | **Python**: 3.8+ (3.12 recommended)
