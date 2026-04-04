# 📡 NewsRadar - AI 新闻雷达

自动采集 AI 领域新闻，通过 Gemini AI 生成中文摘要，部署在 GitHub Pages 上。

**每 30 分钟自动更新。完全免费。**

## 新闻源

| 来源 | 类型 | 说明 |
|------|------|------|
| Hacker News | API | 英文 AI 热帖 |
| arXiv | API | 最新 AI 论文 |
| TechCrunch AI | RSS | AI 产业新闻 |
| The Verge AI | RSS | 科技新闻 |
| MIT Tech Review | RSS | 前沿技术报道 |
| VentureBeat AI | RSS | AI 行业新闻 |
| Ars Technica | RSS | 技术新闻 |
| 机器之心 | RSS | 中文 AI 新闻 |

## 技术栈

- **采集器**: Python + feedparser + httpx
- **AI 摘要**: Google Gemini 2.0 Flash (免费层)
- **前端**: React + TypeScript + Vite + Tailwind CSS
- **CI/CD**: GitHub Actions (每 30 分钟 cron)
- **部署**: GitHub Pages

## 设置

### 1. Fork / Clone

```bash
git clone https://github.com/HackerChi-Hub/NewsRadar.git
cd NewsRadar
```

### 2. 配置 Gemini API Key

1. 前往 [Google AI Studio](https://aistudio.google.com/) 获取免费 API Key
2. 在 GitHub 仓库 Settings → Secrets and variables → Actions → New repository secret
3. 添加 `GEMINI_API_KEY`

### 3. 启用 GitHub Pages

1. 仓库 Settings → Pages
2. Source 选择 **Deploy from a branch**
3. Branch 选择 `gh-pages` / `root`
4. 保存

### 4. 首次运行

前往 Actions tab → "Collect & Deploy" → Run workflow

## 本地开发

```bash
# 采集器
cd collector
uv sync
GEMINI_API_KEY=your_key uv run python main.py

# 前端
cd web
npm install
npm run dev
```

## 成本

**$0** — 全部使用免费服务：
- GitHub Actions: 公共仓库无限分钟
- GitHub Pages: 免费静态托管
- Gemini API: 免费层 1000 次/天
