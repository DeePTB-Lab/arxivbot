# ArXiv Bot

**ArXiv Bot** implements GitHub Actions-based automated deployment to fetch the latest papers from [arXiv](https://arxiv.org), utilizing LLMs for **Deep Scan** to generate expert-level insights (Core Innovations, Key Conclusions, Expert Reviews). It supports notifications via [Lark](https://www.feishu.cn) and **Email**.

Key Highlights:
*   **Deep Scan Analysis**: Automatically downloads source code to read Introduction & Conclusion, generating deep insights beyond simple abstracts.
*   **Multi-Channel Notifications**: Optimized Lark Cards and Email support.
*   **Separated Configuration**: Private config (API Keys) and public config (Keywords/Categories) are separated for better security.
*   **Modern Deployment**: Built with `uv` for lightning-fast Python project management.

## Feature List

- [x] **Core**: Fetch and filter arXiv papers by keywords and LLM relevance.
- [x] **LLM Enhanced**: Abstract Translation (English to Chinese/native).
- [x] **Deep Scan (New)**: Downloads paper source, analyzes Intro & Conclusion, generates **Expert Deep Analysis**.
- [x] **Multi-Channel**: 
  - [x] Lark Custom Bot (Beautiful Card UI)
  - [x] Email Notification (SMTP)
- [x] **Secure Config**: Separation of secrets and rules.
- [x] **History Auto-Push**: Automatically push historical paper records.

## Usage

### 1. Automated Deployment (Recommended: GitHub Actions)

The easiest way to run ArXivToday without a local server.

1. **Fork this repository** to your GitHub account.
2. **Commit Your Rules**:
    *   Edit `data/paper.yaml` to set your **Keywords** and **Categories**.
    *   (Optional) Edit `data/hunt_prompt.md` to customize the LLM filter prompt.
    *   **Important**: These files must be **committed** to the repo.
3. **Configure Secrets**:
    *   Go to your forked repo -> **Settings** -> **Secrets and variables** -> **Actions**.
    *   Click **New repository secret** and add the following (no need for `config.yaml`):
        *   `LARK_WEBHOOK_URL`: Webhook URL for Lark Bot
        *   `LARK_TEMPLATE_ID`: Lark Message Card Template ID
        *   `LARK_TEMPLATE_VERSION`: (Optional) Template Version (default: `1.0.0`)
        *   `LLM_API_KEY`: API Key for your LLM
        *   `LLM_BASE_URL`: Base URL for LLM
        *   `LLM_MODEL`: Model name (e.g. `gpt-4o`, `deepseek-chat`)
        *   `SENDER_EMAIL`: (Optional) Sender email address
        *   `SENDER_PASSWORD`: (Optional) Email App Password
        *   `RECEIVER_EMAIL`: (Optional) Receiver email address
4. **Enable Workflow**:
    *   Go to the **Actions** tab.
    *   Enable "Daily ArXiv Bot" workflow.
    *   It runs automatically at 00:00 UTC (08:00 Beijing Time) every day.

**Note**: When configuring, please delete the `data/paper_history.json` file in your repository to clear the author's search history.

### 2. Lark & Email Configuration Guide

Required for both GitHub Actions and Local Run.

#### A. Lark Bot
1. Add a **Custom Bot** in your Lark group chat and get the **Webhook URL**.
2. Open `data/lark_card.json` and copy its content.
3. Go to Lark [Message Card Builder](https://open.feishu.cn/tool/cardbuilder).
4. Paste the JSON, Save, and Publish to get the **Template ID**.

#### B. Email Notification
1. Prepare an SMTP-enabled email (Gmail, Outlook, etc.).
2. Get an **App Password** (do not use your login password).

### 3. Local Development (Advanced)

If you have your own server or want to debug locally.

#### 1. Installation (Using uv)

```sh
# Install uv
pip install uv

# Clone repo
git clone https://github.com/DeePTB-Lab/arxivbot.git
cd arxivbot

# Sync dependencies
uv sync

# Activate environment (ensure CLI tools can be run from anywhere)
source .venv/bin/activate
```

#### 2. Configuration

For local run, write configs directly to file (do NOT commit `config.yaml`):

```sh
# Copy template
cp data/config.example.yaml data/config.yaml

# Edit secrets (Webhook, API Key, etc.)
vim data/config.yaml

# Edit rules (Keywords)
vim data/paper.yaml
```

#### 3. Run

```sh
# 1. Standard Mode (Abstract Translation + Filtering)
uv run axvbot --use-llm

# 2. Deep Scan Mode (Recommended 🔥)
# Downloads source code, analyzes Intro/Conclusion for deep insights
uv run axvbot --use-llm --deep-scan
```

#### 4. Local Cron Job

```sh
# Edit crontab
crontab -e

# Run daily at 12:24 local time
24 12 * * 1-5 cd /absolute/path/to/arxivbot && uv run axvbot --use-llm --deep-scan >> run.log 2>&1
```

## License

This project is under the [GPL-3.0 License](LICENSE).

## Contact

For any questions, suggestions, or feedback, feel free to submit an issue.
- **GitHub Issues**: [Issues Page](https://github.com/DeePTB-Lab/arxivbot/issues)

## Acknowledgements

This repository was inspired by [ArXivToday-Lark](https://github.com/InfinityUniverse0/ArXivToday-Lark) by InfinityUniverse0. Thanks!
