import { Article, CATEGORY_COLORS, relativeTime } from "../types";

export default function NewsCard({ article }: { article: Article }) {
  const colorClass = CATEGORY_COLORS[article.category] || CATEGORY_COLORS["未分类"];

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-[#12121f] rounded-xl p-5 hover:bg-[#1a1a2e] transition-all duration-200 border border-white/5 hover:border-green-500/20 group"
    >
      {/* Top row: category + source + time */}
      <div className="flex items-center gap-2 mb-3 text-xs">
        <span className={`px-2 py-0.5 rounded-full font-medium ${colorClass}`}>
          {article.category}
        </span>
        <span className="text-gray-500">{article.source}</span>
        <span className="text-gray-600 ml-auto shrink-0">
          {relativeTime(article.published)}
        </span>
      </div>

      {/* Title */}
      <h3 className="font-semibold text-[15px] leading-snug mb-2 group-hover:text-green-400 transition-colors">
        {article.title_zh}
      </h3>

      {/* English original title (smaller) */}
      {article.title_zh !== article.title && (
        <p className="text-xs text-gray-600 mb-2 line-clamp-1">
          {article.title}
        </p>
      )}

      {/* Summary */}
      <p className="text-sm text-gray-400 leading-relaxed line-clamp-3">
        {article.summary_zh}
      </p>

      {/* Tags */}
      {article.tags.length > 0 && (
        <div className="flex gap-1.5 mt-3 flex-wrap">
          {article.tags.map((tag) => (
            <span
              key={tag}
              className="text-[11px] text-gray-500 bg-white/5 px-2 py-0.5 rounded-full"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </a>
  );
}
