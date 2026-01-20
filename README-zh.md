
# ArXiv Bot

**ArXiv Bot** 实现了基于Github Actions的自动化部署，自动从 [arXiv](https://arxiv.org) 获取最新论文，还集成 LLM 进行**深度扫描（Deep Scan）**，生成专家级论文解读（包含核心创新、关键结论、专家点评）。支持推送到 [飞书](https://www.feishu.cn) 群聊和**邮件**订阅。

其主要特点包括：
*   **Deep Scan 深度分析**：利用 LLM 自动下载并读取论文全文（Introduction & Conclusion），生成超越摘要的深度解读。
*   **多渠道通知**：支持飞书卡片和邮件通知。
*   **配置分离**：私有配置（API Key、密钥）与公开配置（关键词、Tag）分离，便于管理。
*   **极简部署**：基于 `uv` 的现代化 Python 项目管理，一键运行。

## 功能列表

- [x] **基础功能**: 按关键词自动抓取并通过 LLM 筛选 arXiv 论文
- [x] **LLM 增强**: 摘要翻译（中英对照）
- [x] **Deep Scan (新)**: 自动下载源码，深入阅读引言与结论，生成**专家级深度解读**
- [x] **多渠道推送**: 
  - [x] 飞书自定义机器人（美观消息卡片）
  - [x] 邮件通知（SMTP 支持）
- [x] **配置分离**: 敏感信息与订阅规则分离
- [x] **历史自动推送**: 自动推送历史论文记录

## 使用方法

### 1. 自动化部署 (推荐: GitHub Actions)

这是最省心的使用方式，依靠 GitHub 免费的 Actions 资源每日自动运行，无需本地服务器。


1. **Fork 本仓库** 到你的 GitHub 账号。
2. **提交搜索规则**:
    *   修改 `data/paper.yaml`，填入你关注的 **Keywords** (关键词) 和 **Categories** (分类)。
    *   (可选) 修改 `data/hunt_prompt.md` 自定义 LLM 筛选提示词。
    *   **重要**: 这些文件需要**提交**到仓库中，Bot 运行时会读取仓库文件。
3. **配置敏感信息 (Secrets)**:
    *   进入你 Fork 后的仓库页面，点击 **Settings** -> **Secrets and variables** -> **Actions**。
    *   点击 **New repository secret**，添加以下变量 (无需 `config.yaml` 文件):
        *   `LARK_WEBHOOK_URL`: 飞书机器人 Webhook 地址
        *   `LARK_TEMPLATE_ID`: 飞书消息卡片 Template ID
        *   `LLM_API_KEY`: LLM 的 API Key
        *   `LLM_BASE_URL`: LLM 的 Base URL
        *   `LLM_MODEL`: 模型名称 (如 `gpt-4o`, `deepseek-chat`)
        *   `SENDER_EMAIL`: (可选) 发件人邮箱
        *   `SENDER_PASSWORD`: (可选) 邮箱应用专用密码
        *   `RECEIVER_EMAIL`: (可选) 收件人邮箱
4. **启用 Workflow**:
    *   进入 **Actions** 标签页。
    *   启用 "Daily ArXiv Bot" 工作流。
    *   它将默认在每天 UTC 00:00 (北京时间 08:00) 自动运行。

**note** 配置时，请删除仓库中原有的 data/paper_history.json 文件来清空本作者的检索历史。

### 2. 飞书与邮件配置指南

无论使用 GitHub Actions 还是本地运行，你都需要先获取相关的 ID 和 密钥。

#### A. 飞书机器人 (Lark Bot)
1. 在飞书群聊中添加**自定义机器人**，获取 **Webhook URL**。
2. 打开 `data/lark_card.json` 文件，复制全部内容。
3. 进入飞书 [消息卡片搭建工具](https://open.feishu.cn/tool/cardbuilder)。
4. 粘贴 JSON 内容，保存并发布，获取 **Template ID**。

#### B. 邮件通知 (Email)
1. 准备支持 SMTP 的邮箱 (Gmail, QQ, 163 等)。
2. 开启 SMTP 服务并获取 **应用专用密码** (App Password)。
   *   *注意：不要直接使用邮箱登录密码。*

### 3. 本地开发与运行 (高级选项)

仅供有服务器或需要本地调试的开发者使用。

#### 1. 环境安装 (使用 uv)

```sh
# 安装 uv
pip install uv

# 克隆项目
git clone https://github.com/DeePTB-Lab/arxivbot.git
cd arxivbot

# 同步环境
uv sync

# 激活环境（保证命令行工具可以在任意位置执行）
source .venv/bin/activate
```

#### 2. 配置文件

本地运行时，配置直接写入文件 (注意不要提交 `config.yaml`):

```sh
# 复制模版, 
cp data/config.example.yaml data/config.yaml

# 编辑配置 (填入 Webhook, API Key, 邮箱 等)
vim data/config.yaml

# 编辑搜索规则 (填入 Keywords)
vim data/paper.yaml

# 编辑 LLM 筛选提示词。
vim data/hunt_prompt.md
```

#### 3. 运行脚本

```sh
# 1. 常规模式 (仅摘要翻译 + 筛选)
uv run axvbot --use-llm

# 2. 深度扫描模式 (推荐 🔥)
# 会下载论文源码，深入分析引言和结论，生成专家级解读
uv run axvbot --use-llm --deep-scan
```

#### 4. 本地定时任务 (Crontab)

```sh
# 编辑 crontab
crontab -e

# 添加每日 12:24 运行的任务
24 12 * * 1-5 cd /absolute/path/to/arxivbot && uv run axvbot --use-llm --deep-scan >> run.log 2>&1
```

## 自定义扩展

可以在本项目的基础上进行自定义扩展。比如：

- 你可以自行定义消息卡片的样式，或采用其他消息类型。
- 可以使用飞书的 [应用机器人](https://open.feishu.cn/document/client-docs/bot-v3/bot-overview)，以实现更交互式的工作流。
- 可以扩展 `src/core/notifier.py` 支持更多通知渠道（如 Slack, Telegram）。

## 许可证

本项目基于 [GPL-3.0 许可证](LICENSE)。

## 联系方式

如有任何问题、建议或反馈，欢迎提交 issue。
- **GitHub 问题反馈**: [问题页面](https://github.com/DeePTB-Lab/arxivbot/issues)

## 致谢
本仓库受到了 InfinityUniverse0 的 [ArXivToday-Lark](https://github.com/InfinityUniverse0/ArXivToday-Lark) 的启发，感谢!
