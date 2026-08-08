"use client";

import { ExternalLink } from "lucide-react";

import type { NewsArticle } from "@/lib/api";

function publishedLabel(value: string): string {
  return new Intl.DateTimeFormat("zh-TW", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function sentimentLabel(value: NewsArticle["sentiment"]): string {
  if (value === "Positive") return "正向";
  if (value === "Negative") return "負向";
  return "中性";
}

export default function NewsTimeline({ articles }: { articles: NewsArticle[] }) {
  return (
    <div className="news-list">
      {articles.map((article) => (
        <article className="news-item" key={`${article.url}-${article.published_at}`}>
          <div className="news-meta">
            <span className="news-category">{article.category}</span>
            <span>{publishedLabel(article.published_at)}</span>
            <span>{article.source}</span>
          </div>
          <div className="news-body">
            <div>
              <h3>{article.headline}</h3>
              {article.summary && <p>{article.summary}</p>}
            </div>
            <a href={article.url} target="_blank" rel="noreferrer" aria-label="閱讀新聞原文">
              <ExternalLink size={16} strokeWidth={1.5} aria-hidden="true" />
            </a>
          </div>
          <div className="news-footer">
            <span className={`sentiment ${article.sentiment.toLowerCase()}`}>
              {sentimentLabel(article.sentiment)} · 信心 {(article.sentiment_confidence * 100).toFixed(0)}%
            </span>
            <span>重要度 {article.importance}/5</span>
          </div>
        </article>
      ))}
    </div>
  );
}
