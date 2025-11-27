# GitHub Enterprise Inventory - Quick Start Guide

Get up and running in **15 minutes** with this streamlined setup guide.

> **Need More Details?** See [README.md](README.md) for comprehensive documentation including troubleshooting, API endpoints, and security best practices.

## Prerequisites

- **GitHub Enterprise** account with admin access
- **15 minutes** of your time
- **Internet connection**

## 5-Step Setup

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

## Output Files

### Repository CSV (24 columns)
Key data: Org, Repo name, Visibility, Size, Language, Workflows, Branches, Tags, Runners, Webhooks, Forks, Stars, etc.

### Organization CSV (15 columns)
Key data: Org name, Total repos, Total teams, Webhooks, Apps, Self-hosted runners, GitHub-hosted runners, etc.

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| **Runners show 0** but exist | Edit token in GitHub → Add `admin:org` scope → Update token |
| **"No organizations found"** | Add `admin:enterprise` scope to token |
| **Rate limit errors** | Create more tokens, add to `.env` comma-separated |
| **"ModuleNotFoundError"** | Run `pip install -r requirements.txt` |
| **Script hangs** | Large enterprise? Can take 30-60 min. Check `output/logs/*.log` |

---

## Testing Mode

To test with just 1 organization before running full inventory:

1. Edit `.env` file
2. Set: `MAX_ORGS_TO_PROCESS=1`
3. Run: `python github_inventory.py`
4. Verify output looks correct
5. Set `MAX_ORGS_TO_PROCESS=0` (or remove line) for full run

---

## Important Notes

### Runner Data Requires `admin:org` Scope
- Self-hosted runners: `Org_Runners_SelfHosted`, `Repo_Runners`
- GitHub-hosted runners: `Org_Runners_GitHubHosted`
- Without `admin:org`, all runner counts will be **0**

### Security
- ✅ Never commit `.env` file (already in `.gitignore`)
- ✅ Store tokens securely
- ✅ Rotate tokens every 90 days
- ❌ Don't share tokens via email/chat

### Performance
- **Small** (< 100 repos): 5-10 minutes
- **Medium** (100-500 repos): 15-30 minutes
- **Large** (500+ repos): 30-60+ minutes
- Use multiple tokens for 5x faster execution

---

## Next Steps

✅ **You're done!** The CSV files in `output/` folder contain your complete inventory.

📖 **Need more details?**
- Full documentation: [README.md](README.md)
- Troubleshooting guide: See "Troubleshooting" section in README.md
- PAT scope reference: See "GitHub Personal Access Token (PAT) Setup" in README.md

---

**Version**: 2.0 | **Last Updated**: November 2025 | **Python**: 3.8+ (3.12 recommended)
