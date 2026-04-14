"""Keyword-based domain & category detection. No API needed.

Fixes:
- categorize() now returns domain-default category instead of "未分类" when no keywords match.
- detect_domain() now scores by unique keyword presence, not raw counts (avoids bias toward long titles).
- Added fallback chain so articles always get a meaningful category.
"""

from __future__ import annotations

# ── Domain keywords (top-level classification) ────────────────────
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "AI": [
        # English
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "neural", "llm", "large language model", "gpt", "chatgpt", "openai",
        "anthropic", "claude", "gemini", "mistral", "llama", "deepseek",
        "transformer", "diffusion", "midjourney", "dall-e", "sora",
        "copilot", "rag", "fine-tuning", "nlp", "computer vision",
        "artificial intelligence", "generative ai", "genai",
        "multi-modal", "multimodal", "agentic",
        # Chinese
        "人工智能", "大模型", "机器学习", "深度学习", "语言模型",
        "智能体", "agent", "多模态", "生成式 AI", "AI 模型",
        "通义", "千问", "文心", "智谱", "讯飞",
        "端侧 AI", "嵌入式 AI", "AI 芯片",
    ],
    "安全": [
        # English
        "security", "vulnerability", "cve", "exploit", "malware",
        "ransomware", "phishing", "breach", "hack", "cyber",
        "zero-day", "0day", "apt", "ddos", "botnet", "backdoor",
        "firewall", "encryption", "privacy", "data breach",
        "cyberattack", "infosec", "threat", "malware", "virus",
        # Chinese
        "漏洞", "攻击", "安全", "恶意", "勒索", "钓鱼",
        "数据泄露", "入侵", "威胁", "防火墙", "加密",
        "渗透", "红队", "蓝队", "ctf", "pentest", "应急响应",
        "网络安全", "信息安全", "隐私保护", "数据安全",
    ],
    "经济": [
        # English
        "economy", "gdp", "inflation", "interest rate", "federal reserve",
        "stock", "market", "nasdaq", "s&p", "dow jones", "ipo",
        "crypto", "bitcoin", "ethereum", "blockchain",
        "recession", "tariff", "trade war", "bond", "yield",
        # Chinese
        "经济", "gdp", "通胀", "降息", "加息", "美联储", "央行",
        "股市", "股票", "纳斯达克", "上证", "港股", "基金",
        "加密货币", "比特币", "以太坊", "区块链", "融资", "估值",
        "上市", "ipo", "并购", "收购", "财报", "汇率",
    ],
    "科技": [
        # English
        "software", "hardware", "chip", "semiconductor", "cpu", "gpu",
        "apple", "google", "microsoft", "amazon", "meta", "tesla", "nvidia",
        "iphone", "android", "ios", "linux", "windows",
        "cloud", "saas", "devops", "kubernetes", "docker",
        "5g", "6g", "quantum", "smartphone", "laptop",
        # Chinese
        "软件", "硬件", "芯片", "半导体", "处理器", "显卡",
        "手机", "电脑", "操作系统", "云计算", "数据库",
        "开源", "github", "开发者", "编程", "框架",
        "服务器", "数据中心", "互联网", "平台",
    ],
    "国际": [
        # English
        "united nations", "un ", "nato", "g7", "g20", "summit",
        "diplomat", "diplomacy", "treaty", "sanction", "tariff",
        "trade war", "bilateral", "multilateral", "geopolitic",
        "climate", "carbon", "emission", "cop", "paris agreement",
        "who", "world health", "pandemic", "vaccine",
        "space", "nasa", "esa", "spacex", "rocket", "satellite",
        "middle east", "ukraine", "russia", "china", "taiwan",
        # Chinese
        "联合国", "峰会", "外交", "贸易", "关税", "制裁",
        "气候", "碳排放", "世卫", "国际", "全球",
        "太空", "航天", "卫星", "火箭", "中东", "乌克兰",
        "欧盟", "东盟", "非洲", "美国", "英国", "日本", "韩国",
    ],
}

# ── Category keywords (sub-classification per domain) ─────────────
CATEGORY_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "AI": {
        "LLM": [
            "llm", "large language model", "gpt", "chatgpt", "claude",
            "gemini", "mistral", "llama", "deepseek", "qwen", "通义",
            "千问", "文心", "智谱", "大模型", "语言模型", "chatbot", "对话",
            "prompt", "rag", "fine-tuning", "微调", "token", "transformer",
            "reasoning", "推理", "alignment", "对齐", "sft", "rlhf",
            "moe", "mixture of experts", "model context", "context window",
            "o1", "o3", "claude 3", "gpt-4", "gpt-5",
        ],
        "CV": [
            "computer vision", "image generation", "video generation",
            "diffusion", "stable diffusion", "midjourney", "dall-e", "sora",
            "图像", "视觉", "视频生成", "图片生成", "文生图", "文生视频",
            "segmentation", "ocr", "目标检测", "人脸识别",
            "3d", "nerf", "gaussian splatting", "multimodal", "多模态",
            "vit", "生成式 AI", "image gen", "video gen",
        ],
        "机器人": [
            "robot", "robotics", "humanoid", "autonomous driving",
            "self-driving", "自动驾驶", "机器人", "无人机", "drone",
            "embodied", "具身", "智能机器人", "机器狗", "机械臂",
        ],
        "AI产品": [
            "product", "app launch", "release", "上线", "发布",
            "产品", "应用", "工具", "copilot", "智能体",
            "assistant", "api", "定价", "付费", "免费",
            "launch", "announce", "unveil", "debut",
            "上线", "推出", "正式版", "available now", "generally available",
        ],
        "研究突破": [
            "breakthrough", "sota", "state-of-the-art", "record",
            "first to", "outperform", "surpass", "exceed",
            "突破", "超越", "刷新", "首次", "最强",
            "new architecture", "novel method", "improves",
            "benchmark", "rank 1", "top of", "best",
        ],
        "行业": [
            "industry", "startup", "company", "funding", "investor",
            "行业", "公司", "融资", "投资", "创业", "独角兽",
            "venture", "series a", "series b", "acquisition", "merger",
            "生态", "商业化", "落地", "应用",
        ],
        "政策": [
            "regulation", "policy", "law", "act", "ban", "restrict",
            "governance", "compliance", "audit",
            "监管", "法规", "政策", "法案", "合规", "审查",
            "eu ai act", "white house ai", "un ai",
            "政府", "监管机构", "数据局",
        ],
        "开源": [
            "open source", "open-source", "github", "开源", "开放",
            "weights", "model release", "模型开源",
            "apache", "mit license", "bsd", "open weights",
        ],
    },
    "安全": {
        "漏洞": [
            "vulnerability", "cve", "zero-day", "0day", "exploit",
            "patch", "漏洞", "补丁", "远程代码执行", "rce",
            "buffer overflow", "sql injection", "xss", "csrf",
            "缓冲区溢出", "注入", "跨站", "修复", "cve-",
        ],
        "攻击": [
            "attack", "apt", "hack", "breach", "intrusion",
            "red team", "penetration", "攻击", "入侵", "渗透",
            "红队", "蓝队", "应急响应", "取证",
            "ddos", "勒索软件", "供应链攻击",
        ],
        "隐私合规": [
            "privacy", "data breach", "leak", "surveillance",
            "数据泄露", "隐私", "监控", "合规", "gdpr",
            "个人信息", "数据保护", "网络安全法",
        ],
        "安全工具": [
            "tool", "scanner", "firewall", "antivirus", "edr",
            "siem", "waf", "ids", "ips", "工具", "防护",
            "安全框架", "安全协议", "加密算法",
        ],
    },
    "经济": {
        "宏观": [
            "gdp", "inflation", "interest rate", "federal reserve",
            "economy", "recession", "growth", "经济", "通胀",
            "降息", "加息", "美联储", "央行", "gdp",
            "宏观经济", "财政政策", "货币政策", "刺激计划",
        ],
        "市场": [
            "stock", "market", "nasdaq", "s&p", "dow", "ipo",
            "earnings", "股市", "股票", "纳斯达克", "港股",
            "上证", "财报", "涨", "跌", "市值",
            "trading", "index", "指数", "交易日",
        ],
        "投融资": [
            "funding", "startup", "venture", "acquisition",
            "merger", "valuation", "融资", "投资", "收购",
            "估值", "独角兽", "上市", "ipo",
            "series a", "series b", "pre-a", "a轮", "b轮",
        ],
        "加密货币": [
            "crypto", "bitcoin", "ethereum", "blockchain",
            "defi", "nft", "web3", "比特币", "以太坊",
            "区块链", "加密货币", "交易所", "稳定币",
        ],
    },
    "科技": {
        "软件": [
            "software", "app", "update", "release", "os",
            "windows", "macos", "linux", "android", "ios",
            "browser", "软件", "应用", "更新", "操作系统",
            "版本", "升级", "beta", "正式版",
        ],
        "硬件": [
            "hardware", "chip", "semiconductor", "cpu", "gpu",
            "phone", "laptop", "tablet", "芯片", "半导体",
            "处理器", "手机", "电脑", "显卡", "内存",
            "nvidia", "amd", "intel", "高通", "联发科",
        ],
        "互联网": [
            "internet", "cloud", "saas", "platform", "social",
            "streaming", "互联网", "云计算", "平台", "社交",
            "流媒体", "电商", "搜索", "社交媒体",
        ],
        "开发者": [
            "developer", "programming", "framework", "api",
            "devops", "kubernetes", "docker", "开发者", "编程",
            "框架", "数据库", "代码", "开源",
            "javascript", "python", "rust", "java", "前端", "后端",
        ],
    },
    "国际": {
        "外交": [
            "diplomat", "diplomacy", "summit", "bilateral",
            "ambassador", "外交", "峰会", "会晤", "大使",
            "访问", "协议", "条约", "谈判",
        ],
        "贸易": [
            "trade", "tariff", "sanction", "export", "import",
            "wto", "贸易", "关税", "制裁", "出口", "进口",
            "贸易战", "进出口", "关税壁垒",
        ],
        "气候": [
            "climate", "carbon", "emission", "renewable", "solar",
            "wind energy", "cop", "气候", "碳", "排放",
            "可再生", "新能源", "碳中和", "绿色能源",
        ],
        "太空科学": [
            "space", "nasa", "esa", "spacex", "rocket", "satellite",
            "who", "health", "vaccine", "太空", "航天",
            "卫星", "火箭", "世卫", "疫苗",
            "月球", "火星", "探测器", "轨道",
        ],
    },
}

# Domain-level fallback categories (used when no sub-keywords match)
DOMAIN_DEFAULT_CATEGORY: dict[str, str] = {
    "AI": "LLM",
    "安全": "攻击",
    "经济": "市场",
    "科技": "互联网",
    "国际": "外交",
}


def _score_text(text: str, keywords: list[str]) -> int:
    """Count how many keywords appear in text (case-insensitive)."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw.lower() in text_lower)


def detect_domain(title: str, content: str = "") -> str:
    """Detect top-level domain. Returns 'AI', '安全', '经济', '科技', or '科技'."""
    text = (title + " " + (content or "")).lower()
    scores: dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = _score_text(text, keywords)

    best_domain = max(scores, key=lambda d: scores[d])
    best_score = scores[best_domain]

    # Require at least 1 keyword match; otherwise default to "科技"
    if best_score == 0:
        return "科技"
    return best_domain


def categorize(title: str, content: str = "", domain: str = "") -> str:
    """Categorize within a domain. Returns best sub-category, or domain-default if no sub-keywords match."""
    if not domain:
        domain = detect_domain(title, content)

    text = (title + " " + (content or "")).lower()

    cats = CATEGORY_KEYWORDS.get(domain, {})
    if not cats:
        # Unknown domain — use it directly as category
        return domain

    best_cat = DOMAIN_DEFAULT_CATEGORY.get(domain, "行业")
    best_score = 0

    for cat, keywords in cats.items():
        score = _score_text(text, keywords)
        if score > best_score:
            best_score = score
            best_cat = cat

    # If no sub-keywords matched, return the domain-default category
    # (e.g., "LLM" for AI, "攻击" for 安全)
    return best_cat
