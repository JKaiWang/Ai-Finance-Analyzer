from datetime import date as date_type
from typing import Any, Literal

from pydantic import BaseModel, Field


class MetricValue(BaseModel):
    value: float | int | str | None = Field(description="標準化後的指標值。")
    period: str | None = Field(
        default=None, description="資料期間，例如 FY2025 或 5y。"
    )
    as_of: date_type | None = Field(default=None, description="資料有效日期。")
    source: str = Field(description="資料來源。")
    is_estimated: bool = Field(default=False, description="是否為估算值。")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="額外資料品質資訊。"
    )


class DataQualitySnapshot(BaseModel):
    source: str = Field(description="主要資料來源。")
    as_of: date_type | None = Field(default=None, description="最新資料有效日期。")
    period: str = Field(description="市場資料期間。")
    metrics: dict[str, MetricValue] = Field(description="指標資料品質與期間資訊。")


class DataStatus(BaseModel):
    status: Literal["available", "partial", "unavailable"] = Field(
        description="資料服務狀態。"
    )
    source: str = Field(description="資料來源。")
    as_of: date_type | None = Field(default=None, description="最新資料有效日期。")
    message: str | None = Field(default=None, description="資料狀態訊息。")
    missing_fields: list[str] = Field(
        default_factory=list, description="目前沒有可用值的欄位。"
    )
