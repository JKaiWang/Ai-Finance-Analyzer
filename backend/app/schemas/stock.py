from datetime import date as date_type

from pydantic import BaseModel, Field

from app.schemas.metrics import DataQualitySnapshot


class PriceRecord(BaseModel):
    date: date_type = Field(description="交易日期。")
    open: float = Field(description="開盤價。")
    high: float = Field(description="當日最高價。")
    low: float = Field(description="當日最低價。")
    close: float = Field(description="收盤價。")
    adjusted_close: float = Field(description="調整後收盤價。")
    volume: int = Field(description="成交量；資料缺失時以 0 表示。")


class StockResponse(BaseModel):
    symbol: str = Field(description="標準化後的股票代號。", examples=["NVDA"])
    company_name: str | None = Field(
        default=None,
        description="公司名稱；來源未提供時為 null。",
    )
    currency: str | None = Field(
        default=None,
        description="報價幣別，例如 USD 或 TWD。",
    )
    current_price: float | None = Field(
        default=None,
        description="目前價格；來源未提供時使用最新收盤價，仍無法取得時為 null。",
    )
    market_cap: int | None = Field(
        default=None,
        description="公司市值；來源未提供時為 null。",
    )
    enterprise_value: int | None = Field(default=None, description="企業價值。")
    shares_outstanding: int | None = Field(default=None, description="流通在外股數。")
    float_shares: int | None = Field(default=None, description="可流通股數。")
    sector: str | None = Field(default=None, description="公司所屬產業部門。")
    industry: str | None = Field(default=None, description="公司所屬細分產業。")
    country: str | None = Field(default=None, description="公司所在國家。")
    exchange: str | None = Field(default=None, description="股票交易所。")
    data_quality: DataQualitySnapshot | None = Field(
        default=None, description="資料來源、期間與品質資訊。"
    )
    history: list[PriceRecord] = Field(
        description="最近一年的每日 OHLCV 歷史資料。",
    )
