"""Keyword-based domain & category detection. No API needed."""

# ── Domain keywords (top-level classification) ────────────────────
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "AI": [
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "neural", "llm", "large language model", "gpt", "chatgpt", "openai",
        "anthropic", "claude", "gemini", "mistral", "llama", "deepseek",
        "transformer", "diffusion", "midjourney", "dall-e", "sora",
        "copilot", "rag", "fine-tuning", "nlp", "computer vision",
        "人工智能", "大模型", "机器学习", "深度学习", "语言模型",
        "智能体", "agent", "多模态",
    ],
    "安全": [
        "security", "vulnerability", "cve", "exploit", "malware",
        "ransomware", "phishing", "breach", "hack", "cyber",
        "zero-day", "0day", "apt", "ddos", "botnet", "backdoor",
        "firewall", "encryption", "漏洞", "攻击", "安全", "恶意",
        "勒索", "钓鱼", "数据泄露", "入侵", "威胁", "防火墙",
        "加密", "渗透", "红队", "蓝队", "ctf", "pentest",
    ],
    "经济": [
        "economy", "gdp", "inflation", "interest rate", "federal reserve",
        "stock", "market", "nasdaq", "s&p", "dow jones", "ipo",
        "crypto", "bitcoin", "ethereum", "blockchain",
        "经济", "gdp", "通胀", "降息", "加息", "美联储", "央行",
        "股市", "股票", "纳斯达克", "上证", "港股", "基金",
        "加密货币", "比特币", "区块链", "融资", "估值",
    ],
    "科技": [
        "software", "hardware", "chip", "semiconductor", "cpu", "gpu",
        "apple", "google", "microsoft", "amazon", "meta", "tesla",
        "iphone", "android", "ios", "linux", "windows",
        "cloud", "saas", "devops", "kubernetes", "docker",
        "5g", "6g", "quantum", "芯片", "半导体", "处理器",
        "手机", "电脑", "操作系统", "云计算", "数据库",
        "开源", "github", "开发者", "编程", "框架",
    ],
    "国际": [
        "united nations", "un", "nato", "g7", "g20", "summit",
        "diplomat", "diplomacy", "treaty", "sanction", "tariff",
        "trade war", "bilateral", "multilateral", "geopolitic",
        "climate", "carbon", "emission", "cop", "paris agreement",
        "who", "world health", "pandemic", "vaccine",
        "space", "nasa", "esa", "spacex", "rocket", "satellite",
        "联合国", "峰会", "外交", "贸易", "关税", "制裁",
        "气候", "碳排放", "世卫", "国际", "全球",
        "太空", "航天", "卫星", "火箭",
        "欧盟", "东盟", "中东", "非洲",
    ],
}

# ── Category keywords (sub-classification per domain) ─────────────
CATEGORY_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "AI": {
        "LLM": [
            "llm", "large language model", "gpt", "chatgpt", "claude",
            "gemini", "mistral", "llama", "deepseek", "qwen", "通义",
            "千问", "文心", "大模型", "语言模型", "chatbot", "对话",
            "prompt", "rag", "fine-tuning", "微调", "token", "transformer",
            "reasoning", "推理", "alignment", "对齐", "sft", "rlhf",
            "moe", "mixture of experts",
        ],
        "CV": [
            "computer vision", "image generation", "video generation",
            "diffusion", "stable diffusion", "midjourney", "dall-e", "sora",
            "图像", "视觉", "视频生成", "图片生成", "segmentation",
            "3d", "nerf", "gaussian splatting", "multimodal", "多模态",
            "vit", "ocr", "文生图",
        ],
        "机器人": [
            "robot", "robotics", "humanoid", "autonomous driving",
            "self-driving", "自动驾驶", "机器人", "无人机", "drone",
            "embodied", "具身",
        ],
        "AI产品": [
            "product", "app launch", "release", "上线", "发布",
            "产品", "应用", "工具", "copilot", "智能体",
            "assistant", "api", "定价", "付费",
        ],
        "研究突破": [
            "breakthrough", "sota", "state-of-the-art", "record",
            "first to", "outperform", "surpass", "exceed",
            "突破", "超越", "刷新", "首次", "最强",
            "new architecture", "novel method", "improves",
        ],
        "产品发布": [
            "launch", "release", "announce", "debut", "unveil",
            "launching", "releasing", "announcing",
            "发布", "上线", "推出", "开源", "正式版",
            "available now", "generally available", "ga",
        ],
        "社区讨论": [
            "discussion", "debate", "opinion", "analysis",
            "review", "thoughts", "perspective", "critique",
            "讨论", "争议", "观点", "分析", "评测",
            "reddit", "hacker news", "lobste",
        ],
        "AI监管": [
            "regulation", "policy", "law", "act", "ban", "restrict",
            "governance", "compliance", "audit",
            "监管", "法规", "政策", "法案", "合规", "审查",
            "eu ai act", "white house ai", "un ai",
        ],
        "AI工具": [
            "tool", "app", "platform", "api", "sdk",
            "免费", "神器", "效率", "产品力",
            "product hunt", "there's an ai for that",
        ],
        "研究": [
            "paper", "research", "arxiv", "论文", "研究", "benchmark",
            "dataset", "icml", "neurips", "iclr", "cvpr", "acl",
            "sota", "breakthrough", "突破",
        ],
        "开源": [
            "open source", "open-source", "github", "开源", "开放",
            "weights", "model release", "模型开源",
        ],
    },
    "安全": {
        "漏洞": [
            "vulnerability", "cve", "zero-day", "0day", "exploit",
            "patch", "漏洞", "补丁", "远程代码执行", "rce",
            "buffer overflow", "sql injection", "xss",
        ],
        "攻防": [
            "attack", "apt", "hack", "breach", "intrusion",
            "red team", "penetration", "攻击", "入侵", "渗透",
            "红队", "蓝队", "应急响应", "取证",
        ],
        "隐私": [
            "privacy", "data breach", "leak", "surveillance",
            "数据泄露", "隐私", "监控", "合规", "gdpr",
        ],
        "安全工具": [
            "tool", "scanner", "firewall", "antivirus", "edr",
            "siem", "waf", "ids", "ips", "工具", "防护",
        ],
    },
    "经济": {
        "宏观": [
            "gdp", "inflation", "interest rate", "federal reserve",
            "economy", "recession", "growth", "经济", "通胀",
            "降息", "加息", "美联储", "央行", "gdp",
        ],
        "市场": [
            "stock", "market", "nasdaq", "s&p", "dow", "ipo",
            "earnings", "股市", "股票", "纳斯达克", "港股",
            "上证", "财报", "涨", "跌",
        ],
        "投融资": [
            "funding", "startup", "venture", "acquisition",
            "merger", "valuation", "融资", "投资", "收购",
            "估值", "独角兽", "上市",
        ],
        "加密": [
            "crypto", "bitcoin", "ethereum", "blockchain",
            "defi", "nft", "web3", "比特币", "以太坊",
            "区块链", "加密货币",
        ],
    },
    "科技": {
        "软件": [
            "software", "app", "update", "release", "os",
            "windows", "macos", "linux", "android", "ios",
            "browser", "软件", "应用", "更新", "操作系统",
        ],
        "硬件": [
            "hardware", "chip", "semiconductor", "cpu", "gpu",
            "phone", "laptop", "tablet", "芯片", "半导体",
            "处理器", "手机", "电脑", "显卡",
        ],
        "互联网": [
            "internet", "cloud", "saas", "platform", "social",
            "streaming", "互联网", "云计算", "平台", "社交",
            "流媒体",
        ],
        "开发": [
            "developer", "programming", "framework", "api",
            "devops", "kubernetes", "docker", "开发者", "编程",
            "框架", "数据库", "代码",
        ],
    },
    "国际": {
        "外交": [
            "diplomat", "diplomacy", "summit", "bilateral",
            "ambassador", "外交", "峰会", "会晤", "大使",
            "访问", "协议", "条约",
        ],
        "贸易": [
            "trade", "tariff", "sanction", "export", "import",
            "wto", "贸易", "关税", "制裁", "出口", "进口",
        ],
        "气候": [
            "climate", "carbon", "emission", "renewable", "solar",
            "wind energy", "cop", "气候", "碳", "排放",
            "可再生", "新能源",
        ],
        "科学": [
            "space", "nasa", "esa", "spacex", "rocket", "satellite",
            "who", "health", "vaccine", "太空", "航天",
            "卫星", "火箭", "世卫", "疫苗",
        ],
    },
}


def detect_domain(title: str, content: str = "") -> str:
    """Detect top-level domain. Returns 'AI', '安全', '经济', '科技', or '未分类'."""
    text = (title + " " + content).lower()
    scores: dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "科技"


def categorize(title: str, content: str = "", domain: str = "") -> str:
    """Categorize within a domain. Returns best category or '未分类'."""
    if not domain or domain not in CATEGORY_KEYWORDS:
        domain = detect_domain(title, content)
    text = (title + " " + content).lower()
    cats = CATEGORY_KEYWORDS.get(domain, {})
    best_cat = "未分类"
    best_score = 0
    for cat, keywords in cats.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_cat = cat
    return best_cat
