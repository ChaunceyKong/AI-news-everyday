# 飞书 AI 圈 24 小时热点早报定时推送

基于 **AIHOT** 官方公开 API，每天定时抓取过去 24 小时 AI 圈最重要的精选事件与热门动态，排版成高颜值的飞书交互式卡片（Interactive Card），并通过 Webhook 自动推送到飞书群。

---

## 🌟 功能特性

- **零外部依赖**：纯 Python 标准库实现（无需 `pip install requests`，开箱即用）。
- **专业卡片样式**：支持飞书交互式富文本卡片，带日期头、重点标题主链、北京时间、一句话精简摘要及「为什么值得关注」。
- **安全校验支持**：同时支持无校验及 HMAC-SHA256 签名校验密钥。
- **多种运行方式**：
  - 本地 Windows 计划任务（开机后台静默运行，无需保持窗口打开）。
  - GitHub Actions（免电脑开机，纯云端免费定时推送）。
  - 支持演练模式（`--dry-run`）和自定义条数与模式。

---

## 🚀 快速开始

### 1. 配置 Webhook

1. 打开飞书群组，点击群右上角 **「设置」/「...」图标 ->「机器人」->「添加机器人」**。
2. 选择 **「自定义机器人」**，给机器人起名（如 `AI热点早报`），点击添加。
3. 复制生成的 **Webhook 地址**。
4. 将本目录下的 `.env.example` 复制一份并重命名为 `.env`：
   ```bash
   cp .env.example .env
   ```
5. 打开 `.env`，填入你的 Webhook 地址：
   ```env
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx
   FEISHU_SECRET=  # 如果在机器人安全设置勾选了"签名校验"才需填，否则留空
   ```

### 2. 测试运行

- **本地演练（不实际发消息，仅打印卡片结构）：**
  ```powershell
  python push_feishu.py --dry-run
  ```

- **真实推送测试：**
  ```powershell
  python push_feishu.py
  ```
  执行成功后，飞书群将立即收到卡片推送。

---

## ⏰ 配置每日定时推送

你可以根据需求选择以下任一方式：

### 方式一：Windows 本地定时任务（推荐在日常使用的电脑上配置）

本目录提供了自动化配置脚本 `setup_windows_task.ps1`，后台静默执行，无弹窗打扰。

- **默认每天早上 09:00 推送：**
  以管理员身份或普通 PowerShell 运行：
  ```powershell
  powershell -ExecutionPolicy Bypass -File setup_windows_task.ps1
  ```
- **自定义推送时间（例如每天 08:30）：**
  ```powershell
  powershell -ExecutionPolicy Bypass -File setup_windows_task.ps1 -Time 08:30
  ```
- **立即测试触发一次任务：**
  ```powershell
  powershell -ExecutionPolicy Bypass -File setup_windows_task.ps1 -RunNow
  ```
- **删除该定时任务：**
  ```powershell
  powershell -ExecutionPolicy Bypass -File setup_windows_task.ps1 -Uninstall
  ```

---

### 方式二：GitHub Actions 云端定时推送（无需开机，全自动）

如果项目托管在 GitHub 上，可以使用根目录下的 `.github/workflows/feishu_ai_daily.yml`：
1. 在 GitHub 仓库页面进入 **Settings -> Secrets and variables -> Actions**。
2. 点击 **New repository secret**，添加两项：
   - `FEISHU_WEBHOOK_URL`: 你的飞书 Webhook 地址。
   - `FEISHU_SECRET`: 签名密钥（如有）。
3. 每天北京时间早上 09:00（UTC 01:00）GitHub 将自动运行并推送到飞书群。

---

## 🛠️ 参数自定义

`push_feishu.py` 支持以下命令行参数：

| 参数 | 说明 | 默认值 | 示例 |
|---|---|---|---|
| `--mode` | 模式：`selected`（精选）、`hot`（最热榜）、`all`（全量） | `selected` | `--mode hot` |
| `--limit` | 推送条目数量 | `8` | `--limit 10` |
| `--window` | 时间窗口：`24h` 或 `7d` | `24h` | `--window 24h` |
| `--dry-run` | 仅在控制台预览卡片，不发送 | 关闭 | `--dry-run` |
