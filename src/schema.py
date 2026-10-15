from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, ValidationError
import logging

logger = logging.getLogger(__name__)

class MarketTick(BaseModel):
    symbol: str
    price: float = Field(..., gt=0, description="Le prix doit être strictement positif")
    volume: int = Field(..., ge=0, description="Le volume doit être positif ou nul")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("symbol")
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Le symbole ne peut pas être vide")
        return v.strip().upper()

def validate_and_filter_ticks(raw_ticks: list[dict]) -> list[MarketTick]:
    valid_ticks = []
    for index, item in enumerate(raw_ticks):
        try:
            tick = MarketTick(**item)
            valid_ticks.append(tick)
        except ValidationError as e:
            logger.warning(f"Erreur de validation à l'index {index} pour les données {item}: {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue à l'index {index} avec les données {item}: {e}")
            
    return valid_ticks