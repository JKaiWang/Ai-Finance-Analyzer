from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class NewsCategory(StrEnum):
    EARNINGS = "Earnings"
    PRODUCT = "Product"
    REGULATION = "Regulation"
    MANAGEMENT = "Management"
    SUPPLY_CHAIN = "Supply Chain"
    MACROECONOMICS = "Macroeconomics"
    GEOPOLITICS = "Geopolitics"
    OTHER = "Other"


class NewsSentiment(StrEnum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class NewsArticle(BaseModel):
    headline: str = Field(description="新聞標題。")
    source: str = Field(description="新聞來源。")
    published_at: datetime = Field(description="發布時間。")
    url: str = Field(description="新聞原文連結。")
    summary: str | None = Field(default=None, description="新聞摘要。")
    category: NewsCategory = Field(description="事件分類。")
    sentiment: NewsSentiment = Field(description="規則式情緒分類，不代表投資建議。")
    sentiment_confidence: float = Field(description="情緒分類信心分數，介於 0 到 1。")
    importance: int = Field(description="事件重要度，1 到 5。")


class NewsResponse(BaseModel):
    symbol: str = Field(description="股票代號。")
    provider: str = Field(description="新聞資料來源。")
    available: bool = Field(description="新聞服務是否已設定並成功取得資料。")
    message: str | None = Field(default=None, description="資料來源狀態訊息。")
    articles: list[NewsArticle] = Field(description="依時間排序的新聞事件。")
