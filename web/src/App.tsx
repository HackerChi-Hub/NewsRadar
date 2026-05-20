import { useState, useEffect, useMemo, useCallback } from "react";
import NewsCard from "./components/NewsCard";
import { Article, NewsData, CATEGORIES, relativeTime } from "./types";

const DATA_URL = `${import.meta.env.BASE_URL}data/news.json`;
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes

export default function App() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("全部");
  const [lastUpdated, setLastUpdated] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: NewsData = await res.json();
      setArticles(data.articles || []);
      setLastUpdated(data.last_updated || "");
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchData]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { 全部: articles.length };
    for (const a of articles) {
      counts[a.category] = (counts[a.category] || 0) + 1;
    }
    return counts;
  }, [articles]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return articles.filter((a) => {
      if (category !== "全部" && a.category !== category) return false;
      if (!q) return true;
      return (
        a.title_zh.toLowerCase().includes(q) ||
        a.title.toLowerCase().includes(q) ||
        a.summary_zh.toLowerCase().includes(q) ||
        a.tags.some((t) => t.includes(q))
      );
    });
  }, [articles, category, search]);

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Header */}
      <header className="bg-[#0d0d18] border-b border-white/5 sticky top-0 z-10 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="shrink-0">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
                <span className="text-green-400">📡</span> NewsRadar
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                AI 新闻雷达 · 每 30 分钟更新
                {lastUpdated && (
                  <span className="ml-2 text-gray-600">
                    · {relativeTime(lastUpdated)}
                  </span>
                )}
              </p>
            </div>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索新闻..."
              className="bg-white/5 text-gray-200 px-4 py-2 rounded-lg text-sm w-40 sm:w-56 focus:outline-none focus:ring-1 focus:ring-green-500/50 border border-white/5 placeholder-gray-600"
            />
          </div>
        </div>
      </header>

      {/* Category Filter */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 overflow-x-auto">
        <div className="flex gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-all ${
                c === category
                  ? "bg-green-500/15 text-green-400 ring-1 ring-green-500/30 font-medium"
                  : "bg-white/5 text-gray-400 hover:bg-white/10"
              }`}
            >
              {c}
              {categoryCounts[c] ? (
                <span className="ml-1 text-xs opacity-60">
                  {categoryCounts[c]}
                </span>
              ) : null}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-4 pb-16">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 9 }).map((_, i) => (
              <div
                key={i}
                className="bg-[#12121f] rounded-xl p-5 border border-white/5 animate-pulse"
              >
                <div className="flex gap-2 mb-3">
                  <div className="h-5 w-12 bg-white/5 rounded-full" />
                  <div className="h-5 w-20 bg-white/5 rounded" />
                </div>
                <div className="h-5 w-full bg-white/5 rounded mb-2" />
                <div className="h-5 w-3/4 bg-white/5 rounded mb-3" />
                <div className="h-4 w-full bg-white/5 rounded mb-1" />
                <div className="h-4 w-2/3 bg-white/5 rounded" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-400 text-lg mb-2">加载失败</p>
            <p className="text-gray-500 text-sm">{error}</p>
            <button
              onClick={fetchData}
              className="mt-4 px-4 py-2 bg-green-500/10 text-green-400 rounded-lg text-sm hover:bg-green-500/20 transition-colors"
            >
              重试
            </button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-4xl mb-4">🔍</p>
            <p className="text-gray-400">
              {articles.length === 0
                ? "暂无新闻，采集器正在收集中..."
                : "没有匹配的结果"}
            </p>
          </div>
        ) : (
          <>
            <p className="text-xs text-gray-600 mb-4">
              共 {filtered.length} 条新闻
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((article) => (
                <NewsCard key={article.id} article={article} />
              ))}
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center text-xs text-gray-700 py-8 border-t border-white/5">
        NewsRadar · Powered by GitHub Actions + Gemini AI
      </footer>
    </div>
  );
}
