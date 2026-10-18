# dsh-upstream-watch

每 15 分钟检查 [`deepseek-ai/deepseek-harness`](https://github.com/deepseek-ai/deepseek-harness) 的 `dsh-v*` tag，
出现新 tag 时推送 Telegram 并把它记录到 `state/last-tag`（去重）。

- 工作流：`.github/workflows/watch.yml`（仅使用官方 `actions/checkout`，无第三方 action）
- 密钥：仓库 Actions Secrets 里的 `TG_BOT_TOKEN` / `TG_CHAT_ID`，不写入本仓库
- 状态：`state/last-tag`
