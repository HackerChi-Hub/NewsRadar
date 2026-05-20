export interface Article {
  id: string;
  title: string;
  title_zh: string;
  summary_zh: string;
  source: string;
  url: string;
  category: string;
  tags: string[];
  published: string;
  collected: string;
}

export interface NewsData {
  last_updated: string;
  articles: Article[];
}

export const CATEGORIES = [
  "全部",
  "LLM",
  "CV",
  "机器人",
  "AI产品",
  "研究",
  "行业",
  "政策",
  "开源",
] as const;

export const CATEGORY_COLORS: Record<string, string> = {
  LLM: "bg-green-500/20 text-green-400",
  CV: "bg-blue-500/20 text-blue-400",
  机器人: "bg-orange-500/20 text-orange-400",
  AI产品: "bg-purple-500/20 text-purple-400",
  研究: "bg-yellow-500/20 text-yellow-400",
  行业: "bg-cyan-500/20 text-cyan-400",
  政策: "bg-red-500/20 text-red-400",
  开源: "bg-pink-500/20 text-pink-400",
  未分类: "bg-gray-500/20 text-gray-400",
};

export function relativeTime(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  if (isNaN(then)) return "";
  const diff = now - then;

  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时前`;

  const days = Math.floor(hours / 24);
  if (days === 1) return "昨天";
  return `${days} 天前`;
}
