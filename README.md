# 📡 NewsRadar - 新闻雷达

全方位新闻聚合平台，覆盖 **AI · 网络安全 · 经济 · 科技 · 国际** 五大领域。

自动采集 50+ 信源，关键词智能分类，Google 翻译中文标题，AI 生成 Top 10 速报。

**每 30 分钟自动更新 · 完全免费 · 部署在 [hyphentech.top/radar](https://hyphentech.top/radar/)**

## 五大领域

| 领域 | 信源数 | 代表源 |
|------|--------|--------|
| 🤖 AI | **37** | arXiv(5类)、Reddit(9版块)、Hacker News、AI媒体(8)、公司博客(7)、政策(4) |
| 🔒 安全 | 6 | The Hacker News、BleepingComputer、FreeBuf、Krebs on Security |
| 💰 经济 | 3 | Bloomberg Markets、CNBC、Reuters |
| 💻 科技 | 5 | Engadget、Ars Technica、IT之家、MIT Tech Review |
| 🌍 国际 | 7 | UN News、BBC World、NASA、新华网、环球时报 |
| 🌐 综合 | 7 | 36氪、虎嗅、钛媒体、爱范儿（按关键词自动分域） |

## 功能

- **关键词自动分类** — 5 大领域 × 10+ 子类（LLM/CV/研究突破/产品发布/社区讨论/AI监管/...），无需 API，毫秒级
- **Google 翻译** — 英文标题自动翻译为中文（free，无需 API key）
- **AI 速报** — 每个领域 Top 10 重要新闻（Groq Llama 3.3 70B 免费层）
- **多级筛选** — 领域标签 → 子分类标签 → 关键词搜索
- **回溯翻译** — 每次运行补翻 20 篇旧文章
- **信源健康追踪** — 自动记录每个信源的响应状态、HTTP 状态码、响应时间；3 次连续失败标记 degraded 并跳过；DNS 级永久失败自动屏蔽

## 技术栈

- **采集器**: Python + feedparser + httpx + deep-translator
- **AI 摘要**: Groq (首选) + Gemini (备选)，均为免费层
- **分类**: 关键词匹配，零 API 调用
- **前端**: Next.js (集成在 Blog 项目中)
- **CI/CD**: GitHub Actions (每 30 分钟 cron)

## 设置

### 1. Clone

```bash
git clone https://github.com/HackerChi-Hub/NewsRadar.git
cd NewsRadar
```

### 2. 配置 API Keys (GitHub Secrets)

| Secret | 用途 | 获取方式 |
|--------|------|---------|
| `GROQ_API_KEY` | AI 速报 + 摘要（首选） | [console.groq.com](https://console.groq.com/) |
| `GEMINI_API_KEY` | AI 摘要（备选） | [aistudio.google.com](https://aistudio.google.com/) |

两个都免费，无需信用卡。

### 3. 首次运行

Actions tab → "Collect & Deploy" → Run workflow

## 本地开发

```bash
cd collector && uv sync
GROQ_API_KEY=your_key uv run python main.py
```

## 成本

**$0** — GitHub Actions (公共仓库无限) + Groq 免费层 (14400 次/天) + Google Translate (免费)
