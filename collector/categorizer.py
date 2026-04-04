"""Keyword-based article categorization. No API needed."""

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "LLM": [
        "llm", "large language model", "gpt", "chatgpt", "claude", "gemini",
        "openai", "anthropic", "mistral", "llama", "deepseek", "qwen",
        "通义", "千问", "文心", "大模型", "语言模型", "chatbot", "对话",
        "prompt", "rag", "fine-tuning", "微调", "token", "transformer",
        "reasoning", "推理", "hallucination", "幻觉", "alignment", "对齐",
        "sft", "rlhf", "grounding", "in-context", "chain-of-thought",
        "moe", "mixture of experts",
    ],
    "CV": [
        "computer vision", "image generation", "video generation",
        "diffusion", "stable diffusion", "midjourney", "dall-e", "sora",
        "图像", "视觉", "视频生成", "图片生成", "object detection",
        "segmentation", "3d", "nerf", "gaussian splatting", "multimodal",
        "多模态", "vit", "image recognition", "ocr", "文生图", "图生",
    ],
    "机器人": [
        "robot", "robotics", "humanoid", "autonomous driving",
        "self-driving", "自动驾驶", "机器人", "无人机", "drone",
        "embodied", "具身", "manipulation", "locomotion",
    ],
    "AI产品": [
        "product", "app launch", "tool", "release", "上线", "发布",
        "产品", "应用", "工具", "feature", "update", "copilot",
        "agent", "智能体", "assistant", "搜索", "翻译", "api",
        "subscription", "pricing", "定价", "付费", "免费",
    ],
    "研究": [
        "paper", "research", "study", "arxiv", "论文", "研究",
        "实验", "benchmark", "dataset", "数据集", "icml", "neurips",
        "iclr", "cvpr", "acl", "emnlp", "aaai", "icra",
        "sota", "state-of-the-art", "breakthrough", "突破",
    ],
    "行业": [
        "industry", "business", "market", "funding", "startup",
        "acquisition", "ipo", "revenue", "行业", "市场", "融资",
        "投资", "商业", "营收", "收购", "估值", "上市", "盈利",
        "layoff", "裁员", "hiring", "招聘",
    ],
    "政策": [
        "policy", "regulation", "law", "government", "政策", "监管",
        "法规", "合规", "治理", "立法", "ban", "禁止", "审查",
        "copyright", "版权", "privacy", "隐私", "safety", "安全",
        "executive order", "eu ai act",
    ],
    "开源": [
        "open source", "open-source", "github", "开源", "开放",
        "apache", "mit license", "hugging face", "weights",
        "model release", "模型开源", "代码开源",
    ],
}


def categorize(title: str, content: str = "") -> str:
    """Categorize by keyword matching. Returns best category or '未分类'."""
    text = (title + " " + content).lower()
    best_cat = "未分类"
    best_score = 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_cat = cat
    return best_cat
