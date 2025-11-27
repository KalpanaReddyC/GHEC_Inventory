# GitHub Enterprise Inventory Tool

> **Quick Start**: New to this tool? Check [QUICKSTART.md](QUICKSTART.md) for a 5-step setup guide (15 minutes).

A comprehensive Python script to collect detailed inventory data from a GitHub Enterprise using GraphQL and REST APIs. This tool helps assess migration complexity, audit security configurations, and generate reports about your GitHub Enterprise resources.

**Version**: 2.0 | **Last Updated**: November 2025 | **Python**: 3.8+ (3.12 recommended)

## Features

- ✅ **Hybrid API Approach**: Combines GraphQL for bulk data and REST API for specific endpoints
- ✅ **Round-Robin PAT Management**: Automatically rotates between multiple Personal Access Tokens to handle API rate limits
- ✅ **Organized Output**: All output files are automatically organized into folders:
  - `output/` - CSV reports (repositories and organizations)
  - `output/logs/` - Timestamped execution logs
- ✅ **Incremental CSV Writing**: Data is written to CSV files as it's collected, preventing data loss on interruption
- ✅ **Dual-Level Reporting**: Generates separate CSV files for:
  - **Repository-level data**: Detailed metrics for each repository (24 columns)
  - **Organization-level data**: Aggregated summary statistics per organization (15 columns)
- ✅ **Comprehensive Inventory**: Collects detailed metadata including:
  - Repository information (name, visibility, size, language, fork status)
  - Branches and tags count
  - GitHub Actions workflows count
  - **GitHub Actions Runners** (Self-hosted and GitHub-hosted - separate columns)
  - Webhooks (repository and organization level)
  - GitHub Apps installations
  - Pull requests and issues count
  - Releases, stars, forks, and watchers
  - Organization teams count
- ✅ **Comprehensive Logging**: Timestamped log files with detailed execution information
- ✅ **Rate Limit Handling**: Intelligent token rotation and rate limit monitoring
- ✅ **Progress Tracking**: Real-time progress indicators during data collection
- ✅ **Testing Mode**: Optional configuration to process limited organizations for testing

## Prerequisites

### System Requirements
- **Python 3.8 or higher** (Python 3.12 recommended)
- **Operating System**: Windows, macOS, or Linux
- **Internet Connection**: Required for GitHub API access
- **Disk Space**: Minimal (logs and CSV files are small)

### GitHub Requirements
- GitHub Enterprise Cloud account with appropriate access
- Personal Access Tokens (PATs) with the following scopes:
  - `repo` - Full control of private repositories
  - `admin:org` - **REQUIRED** for runner data, webhooks, teams, and apps
  - `admin:enterprise` - Read enterprise profile data
  
> **Important**: Without `admin:org` scope, runner counts will show as 0 even if runners exist.

## Installation

### Step 1: Install Python

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   ```
   Should display: `Python 3.12.x` or similar

#### macOS
1. Using Homebrew (recommended):
   ```bash
   brew install python@3.12
   ```
2. Or download from [python.org](https://www.python.org/downloads/)
3. Verify installation:
   ```bash
   python3 --version
   ```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.12 python3-pip
python3 --version
```

### Step 2: Download the Tool

1. **Clone the repository** (if using Git):
   ```bash
   git clone <repository-url>
   cd GitHub_Inventory
   ```

2. **Or download as ZIP**:
   - Extract the ZIP file
   - Open terminal/command prompt in the extracted folder

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `requests` - HTTP library for API calls
- `python-dotenv` - Environment variable management

## GitHub Personal Access Token (PAT) Setup

### Required Scopes

To collect complete inventory data, your GitHub Personal Access Token needs these scopes:

#### For Basic Inventory Collection:
- **`read:org`** - Read organization membership, teams, and settings
- **`repo`** - Full control of private repositories (required to read repository metadata)
- **`admin:enterprise`** - Read enterprise profile data and organization list

#### For Runner Information (Critical):
- **`admin:org`** - **REQUIRED** to list organization-level runners, webhooks, teams, and apps
  - Without this scope, runner counts will show as **0** even if runners exist
  - Also required for organization webhooks and GitHub Apps data

> **⚠️ Important**: The `admin:org` scope is the most common reason for missing runner data.

### How to Create a PAT

1. **Go to GitHub Settings**:
   - Click your profile picture → **Settings**
   - Scroll to **Developer settings** (bottom left sidebar)
   - Click **Personal access tokens** → **Tokens (classic)**

2. **Generate New Token**:
   - Click **"Generate new token"** → **"Generate new token (classic)"**
   - Give it a descriptive name: `Enterprise Inventory Tool`
   - Set expiration (recommended: 90 days for security)

3. **Select Required Scopes** (check these boxes):
   
   #### ✅ repo (Full control of private repositories)
   - [x] repo
     - [x] repo:status
     - [x] repo_deployment
     - [x] public_repo
     - [x] repo:invite
     - [x] security_events
   
   #### ✅ admin:org (Full control of orgs and teams)
   - [x] admin:org
     - [x] write:org
     - [x] read:org
   
   **This is REQUIRED for**:
   - Organization runners (self-hosted and GitHub-hosted)
   - Repository runners
   - Organization webhooks
   - Organization teams
   - GitHub Apps installations
   
   #### ✅ admin:enterprise (Read enterprise data)
   - [x] admin:enterprise

4. **Generate and Copy Token**:
   - Click **"Generate token"**
   - **Copy the token immediately** (starts with `ghp_`)
   - You won't be able to see it again!

5. **Create Multiple Tokens** (Recommended):
   - Repeat steps 2-4 to create 2-5 tokens with identical scopes
   - Multiple tokens provide 5x more API calls per hour


### PAT Security Best Practices

#### ✅ DO:
- Use tokens with **minimum required scopes** for the task
- Set **expiration dates** on tokens (90 days recommended)
- Store tokens securely (password managers, secret management tools)
- **Rotate tokens regularly** (before expiration)
- Use **multiple tokens** for better rate limit handling
- Delete tokens when no longer needed

#### ❌ DON'T:
- Never commit `.env` file to version control (already in `.gitignore`)
- Don't share PATs via email, chat, or screenshots
- Don't use tokens with more permissions than needed

### Troubleshooting PAT Issues

#### Issue: Runners showing 0 but exist in GitHub UI

**Symptom**:
- GitHub UI shows runners in organization settings
- CSV shows `Org_Runners_SelfHosted: 0` and `Org_Runners_GitHubHosted: 0`

**Solution**:
1. Edit your PAT on GitHub (Settings → Developer settings → PATs)
2. Check the `admin:org` scope (and all sub-scopes)
3. Click "Update token"
4. Run the script again - no need to change the token in `.env`

#### Issue: Cannot access organization data

**Symptom**: "No organizations found" or 403 Forbidden errors

**Solution**:
- Edit PAT and add `read:org` and `admin:enterprise` scopes
- Ensure you're a member of the enterprise

## Configuration

### Step 1: Copy the Example File

```bash
# Windows (Command Prompt)
copy .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env

# macOS/Linux
cp .env.example .env
```

### Step 2: Edit Configuration

Edit `.env` file with your favorite text editor:
- Notepad (Windows)
- VS Code
- TextEdit (macOS)
- nano/vim (Linux)

### Step 3: Update Configuration

```env
# Replace with your actual enterprise name
GITHUB_ENTERPRISE_NAME=my-company

# Add your PATs (comma-separated, no spaces)
GITHUB_PATS=ghp_abc123xyz,ghp_def456uvw,ghp_ghi789rst

# Keep these as-is for GitHub.com Enterprise
GITHUB_API_URL=https://api.github.com
GITHUB_GRAPHQL_URL=https://api.github.com/graphql

# Output files (will be created in output/ folder)
REPO_CSV_FILE=github_inventory_repositories.csv
ORG_CSV_FILE=github_inventory_organizations.csv

# Optional: Test with 1 organization first
MAX_ORGS_TO_PROCESS=1
```

### Step 4: Save the File

> **Security Note**: Never commit the `.env` file to version control! It's already in `.gitignore`.

### Configuration Variables Reference

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `GITHUB_ENTERPRISE_NAME` | Your GitHub Enterprise slug/name | `my-company` | Yes |
| `GITHUB_PATS` | Comma-separated list of Personal Access Tokens | `ghp_abc123,ghp_def456` | Yes |
| `GITHUB_API_URL` | GitHub API base URL | `https://api.github.com` | Yes |
| `GITHUB_GRAPHQL_URL` | GitHub GraphQL endpoint | `https://api.github.com/graphql` | Yes |
| `REPO_CSV_FILE` | Repository-level CSV output filename | `github_inventory_repositories.csv` | Yes |
| `ORG_CSV_FILE` | Organization-level CSV output filename | `github_inventory_organizations.csv` | Yes |
| `MAX_ORGS_TO_PROCESS` | Limit organizations for testing (0 = all) | `1` | No |


## Usage

### Running the Inventory Collection

1. **Open terminal/command prompt** in the project folder

2. **Run the script**:
   ```bash
   # Windows
   python github_inventory.py
   
   # macOS/Linux
   python3 github_inventory.py
   ```

3. **Monitor progress**: The script will display real-time updates:
   ```
   ============================================================
   Starting GitHub Enterprise Inventory Collection
   Enterprise: my-company
   Timestamp: 2025-11-27 10:00:00
   ============================================================
   
   [OK] Initialized repository CSV: output\github_inventory_repositories.csv
   [OK] Initialized organization CSV: output\github_inventory_organizations.csv
   
   Found 185 organizations
   Processing Organization: my-org-1
     [OK] Runners: 5 (Self-hosted: 3, GitHub-hosted: 2)
     [OK] Workflows: 12
     [OK] Webhooks: 3
   
   [1/50] Processing: my-org-1/repo-name
     [OK] Workflows: 2
     [OK] Webhooks: 1
     [OK] Branches: 5
   ```

4. **Wait for completion**: Depending on the enterprise size:
   - Small (< 100 repos): 5-10 minutes
   - Medium (100-500 repos): 15-30 minutes
   - Large (500+ repos): 30-60 minutes

5. **Review output**:
   - CSV files: `output/github_inventory_*.csv`
   - Log file: `output/logs/inventory_YYYYMMDD_HHMMSS.log`

### Testing Mode

Before running a full inventory, test with a single organization:

1. Edit `.env` and uncomment:
   ```env
   MAX_ORGS_TO_PROCESS=1
   ```

2. Run the script to verify configuration

3. Once verified, remove or comment out the line to process all organizations

### What the Script Does

1. **Initialization**:
   - Loads configuration from `.env` file
   - Validates PAT tokens
   - Creates output folders (`output/`, `output/logs/`)
   - Initializes CSV files with headers
   - Creates timestamped log file

2. **Data Collection**:
   - Fetches all organizations in the enterprise
   - For each organization:
     - Collects organization-level metadata (webhooks, apps, teams, **runners**)
     - Fetches all repositories
     - For each repository:
       - Collects repository metadata
       - Counts workflows, webhooks, branches, tags
       - Counts self-hosted runners (repository level)
       - Writes data to repository CSV **immediately** (incremental)
     - Calculates organization-level statistics
     - Writes organization summary to CSV

3. **Completion**:
   - Displays summary statistics
   - Saves final log file
   - Reports output file locations

> **Note**: Data is written incrementally, so if the script is interrupted, you'll have partial data saved.

## Output

The script generates **organized output** in dedicated folders:

### Output Structure
```
GitHub_Inventory/
├── output/
│   ├── github_inventory_repositories.csv    # Repository-level data
│   ├── github_inventory_organizations.csv   # Organization-level data
│   └── logs/
│       └── inventory_20251127_100455.log    # Timestamped execution log
├── github_inventory.py
├── .env
└── README.md
```

### 1. Repository-Level CSV (`output/github_inventory_repositories.csv`)

Detailed information for **each repository** (24 columns):

| Column | Description |
|--------|-------------|
| Organization | Organization login name |
| Repository | Repository name |
| Description | Repository description |
| URL | Repository URL |
| Is_Private | Whether repository is private (True/False) |
| Is_Internal | Whether repository is internal (True/False) |
| Is_Public | Whether repository is public (True/False) |
| Is_Fork | Whether repository is a fork (True/False) |
| Is_Archived | Whether repository is archived (True/False) |
| Created_At | Creation timestamp |
| Updated_At | Last update timestamp |
| Pushed_At | Last push timestamp |
| Size_KB | Repository size in kilobytes |
| Default_Branch | Default branch name (e.g., main, master) |
| Forks | Number of forks |
| Open_Issues | Number of open issues |
| Pull_Requests | Number of pull requests |
| Releases | Number of releases |
| Branches | Total branch count |
| Tags | Total tag count |
| Workflows | Number of GitHub Actions workflows |
| Repo_Webhooks | Repository-level webhooks count |
| **Repo_Runners** | Repository self-hosted runners count |
| GitHub_Apps | Installed GitHub Apps count |

### 2. Organization-Level CSV (`output/github_inventory_organizations.csv`)

Aggregated summary statistics for **each organization** (15 columns):

| Column | Description |
|--------|-------------|
| Organization | Organization login name |
| Description | Organization description |
| URL | Organization URL |
| Created_At | Organization creation timestamp |
| Total_Repositories | Total number of repositories |
| Private_Repositories | Number of private repositories |
| Public_Repositories | Number of public repositories |
| Internal_Repositories | Number of internal repositories |
| Archived_Repositories | Number of archived repositories |
| Fork_Repositories | Number of forked repositories |
| Org_Webhooks | Organization-level webhooks count |
| Org_GitHub_Apps | Organization-level GitHub Apps count |
| Org_Teams | Number of teams in the organization |
| **Org_Runners_SelfHosted** | Self-hosted runners count |
| **Org_Runners_GitHubHosted** | GitHub-hosted runners count |

> **Runner Columns**: Separate columns for self-hosted and GitHub-hosted runners make it easy to analyze runner usage and costs.

### 3. Log Files (`output/logs/inventory_*.log`)

Timestamped execution logs with detailed information:
- Configuration loaded
- Organizations processed
- API calls made
- Errors and warnings
- Summary statistics

Example log filename: `inventory_20251127_100455.log`

### Console Output

The script provides real-time progress updates and a summary at the end:

```
============================================================
INVENTORY SUMMARY
============================================================
Total Repositories:        150
Private Repositories:      120
Internal Repositories:     25
Public Repositories:       5
Archived Repositories:     15
Total Branches:            450
Total Workflows:           87
Total Webhooks:            23
Total GitHub Apps:         0
Total Pull Requests:       234
Total Open Issues:         156
============================================================

[OK] Inventory collection completed successfully!
[OK] Repository data saved to: output\github_inventory_repositories.csv
[OK] Organization data saved to: output\github_inventory_organizations.csv
[OK] Log file saved to: output\logs\inventory_20251127_100455.log
```

## Rate Limit Management

The script includes intelligent rate limit handling:

- **Round-Robin Rotation**: Automatically switches between PATs to maximize throughput
- **Rate Limit Monitoring**: Checks remaining API calls before each request
- **Automatic Token Switching**: Switches to next token when limit is approaching
- **Retry Logic**: Retries failed requests with exponential backoff
- **Console Alerts**: Warns when rate limits are approaching

### Recommended PAT Count

Based on enterprise size:

| Enterprise Size | Repositories | Recommended PATs |
|----------------|--------------|------------------|
| Small | < 100 | 1-2 PATs |
| Medium | 100-500 | 2-3 PATs |
| Large | 500-1000 | 3-5 PATs |
| Very Large | 1000+ | 5+ PATs |

> **Tip**: Use PATs from different GitHub accounts for better rate limit distribution.

## Understanding GitHub Actions Runners

The tool collects data about **two types of runners**:

### Self-Hosted Runners
- Runners you deploy and manage on your own infrastructure
- Can be configured at organization or repository level
- Costs: Infrastructure + maintenance costs
- **CSV Columns**: 
## Troubleshooting

### Common Issues

#### 1. "No organizations found" or "Access Denied"
**Causes**:
- Incorrect enterprise name in `.env`
- PATs missing `admin:enterprise` scope
- No access to the enterprise

**Solutions**:
- Verify `GITHUB_ENTERPRISE_NAME` matches your enterprise slug
- Check PAT scopes include `admin:enterprise`
- Ensure you're a member of the enterprise

#### 2. Runners showing 0 but exist in GitHub UI
**Cause**: PAT missing `admin:org` scope

**Solution**:
- Edit your PAT on GitHub
- Add `admin:org` scope (all sub-items)
- Update the token in `.env` file
- See detailed PAT setup section above for scope requirements

#### 3. Rate limit errors
**Symptoms**:
```
[WARNING] API rate limit approaching for token...
Waiting for rate limit reset...
```

**Solutions**:
- Add more PATs to `.env` file (comma-separated)
- Wait for rate limits to reset (shown in console)
- Use PATs from different GitHub accounts if possible

#### 4. "ModuleNotFoundError: No module named 'requests'"
**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

#### 5. Authentication errors (403 Forbidden)
**Causes**:
- Invalid or expired PAT
- PAT format incorrect
- Missing required scopes

**Solutions**:
- Verify PAT starts with `ghp_`
- Check token hasn't expired in GitHub Settings
- Ensure all required scopes are selected:
  - `repo` (all sub-items)
  - `admin:org` (all sub-items)
  - `admin:enterprise`
- Generate a new token if needed

#### 6. Script hangs or runs very slowly
**Causes**:
- Large enterprise with many repositories
- API rate limits being hit
- Network connectivity issues

**Solutions**:
- Be patient - large enterprises can take 30-60 minutes
- Add more PATs for better rate limit handling
- Check network connection
- Monitor log file for progress: `output/logs/inventory_*.log`

#### 7. Missing workflow/webhook/runner data
**Cause**: Insufficient PAT permissions

**Solution**:
- Ensure PAT has `admin:org` scope for:
  - Organization webhooks
  - GitHub Actions runners
  - Team information
  - GitHub Apps
- Ensure PAT has `repo` scope for:
  - Repository webhooks
  - Workflows
  - Repository runners

#### 8. CSV files not created
**Causes**:
- No write permissions in directory
- Disk space full
- Python file I/O error

**Solutions**:
- Run from a directory where you have write permissions
- Check available disk space
- Check console for error messages

### Getting Help

If issues persist:

1. **Check the log file**: `output/logs/inventory_*.log`
2. **Review PAT permissions**: See "GitHub Personal Access Token (PAT) Setup" section above
3. **Test with single org**: Set `MAX_ORGS_TO_PROCESS=1` in `.env`
4. **Check GitHub status**: https://www.githubstatus.com/

## API Endpoints Used

## Files Included

- `github_inventory.py` - Main script
- `requirements.txt` - Python dependencies
- `.env.example` - Configuration template
- `README.md` - This comprehensive documentation
- `QUICKSTART.md` - Quick 5-step setup guide
- `.gitignore` - Prevents committing sensitive files

## API Endpoints Used

The tool uses the following GitHub API endpoints:

### Enterprise & Organization Endpoints:
- `/enterprises/{enterprise}/organizations` - List organizations (requires `admin:enterprise`)
- `/orgs/{org}/repos` - List repositories (requires `read:org`, `repo`)
- `/orgs/{org}/teams` - List teams (requires `admin:org`)
- `/orgs/{org}/installations` - List installed apps (requires `admin:org`)

### Runner Endpoints:
- `/orgs/{org}/actions/runners` - Self-hosted runners (**Requires `admin:org`**)
- `/orgs/{org}/actions/hosted-runners` - GitHub-hosted runners (**Requires `admin:org`**)
- `/repos/{owner}/{repo}/actions/runners` - Repository self-hosted runners (**Requires `admin:org`**)

### Webhook Endpoints:
- `/orgs/{org}/hooks` - Organization webhooks (requires `admin:org`)
- `/repos/{owner}/{repo}/hooks` - Repository webhooks (requires `repo`)

### Repository Metadata:
- GraphQL API - Bulk repository data (requires `repo`, `read:org`)
- `/repos/{owner}/{repo}/actions/workflows` - Workflow files (requires `repo`)

## PAT Scope Quick Reference

| Feature | Required Scope | Why Needed |
|---------|----------------|------------|
| List organizations | `admin:enterprise` | Access enterprise data |
| List repositories | `repo`, `read:org` | Read private repos and org data |
| Workflow counts | `repo` | Read workflow files |
| Branch/tag counts | `repo` | Access repository metadata |
| Self-hosted runners | `admin:org` | List runners API endpoint |
| GitHub-hosted runners | `admin:org` | List hosted runners API endpoint |
| Organization webhooks | `admin:org` | Admin access to org webhooks |
| Repository webhooks | `repo` | Admin access to repo webhooks |
| Teams | `admin:org` | Read team information |
| GitHub Apps | `admin:org` | List installed apps |

## Security Best Practices

### ✅ DO:
- Store tokens securely (password managers or secret management tools)
- Rotate PATs regularly (every 90 days recommended)
- Use tokens with minimum required scopes
- Delete tokens after use if no longer needed
- Review token access in GitHub Settings regularly

### ❌ DON'T:
- Never commit `.env` file to version control (already in `.gitignore`)
- Don't share PATs via email or chat
- Don't use tokens with more permissions than needed

## Project Structure

```
GitHub_Inventory/
├── github_inventory.py          # Main script
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
├── .env                         # Your configuration (create from .env.example)
├── .gitignore                   # Git ignore rules
├── README.md                    # This comprehensive documentation
├── QUICKSTART.md                # Quick 5-step setup guide
└── output/                      # Created when script runs
    ├── github_inventory_repositories.csv
    ├── github_inventory_organizations.csv
    └── logs/
        └── inventory_*.log      # Timestamped execution logs
```

## Frequently Asked Questions (FAQ)

**Q: How long does it take to run?**  
A: Depends on enterprise size:
- Small (< 100 repos): 5-10 minutes
- Medium (100-500 repos): 15-30 minutes
- Large (500+ repos): 30-60+ minutes

**Q: Can I run it multiple times?**  
A: Yes! Each run creates new CSV files and log files. Previous runs are not overwritten (logs are timestamped).

**Q: What if the script crashes?**  
A: Data is saved incrementally to CSV files, so you'll have partial data. Check the log file for error details.

**Q: Do I need admin access to the enterprise?**  
A: No, but you need `admin:enterprise` scope and access to organizations you want to inventory.

**Q: Can I exclude certain organizations?**  
A: Currently no, but you can use `MAX_ORGS_TO_PROCESS` for testing. Filter the CSV afterward.

**Q: Will this modify anything in GitHub?**  
A: No, this is read-only. It only collects data via API calls.

**Q: Can I run this on a schedule?**  
A: Yes! Use cron (Linux/macOS) or Task Scheduler (Windows) to run automatically.

## Support

For issues, questions, or feature requests:

1. Check this README and `PAT_PERMISSIONS.md`
2. Review the log file in `output/logs/`
3. Try with `MAX_ORGS_TO_PROCESS=1` for testing
4. Contact your GitHub administrator

## License

MIT License - See LICENSE file for details

---

**Version**: 2.0  
**Last Updated**: November 2025  
**Python Version**: 3.8+ (3.12 recommended)  
**API Version**: GitHub REST API v3 + GraphQL
