from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, validator


class ChildRegister(BaseModel):
    """Schema for registering a new child."""
    name: str = Field(..., min_length=1, max_length=255, description="Child's name")
    sex: Literal["Male", "Female"] = Field(..., description="Child's sex")
    birth_date: date = Field(..., description="Child's birth date (YYYY-MM-DD)")

    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v > date.today():
            raise ValueError('Birth date cannot be in the future')
        return v


class ChildResponse(BaseModel):
    """Schema for child information response."""
    model_config = ConfigDict(from_attributes=True)
    
    child_id: UUID
    name: str
    sex: str
    birth_date: date
    created_at: datetime


class ChildListResponse(BaseModel):
    """Schema for listing children."""
    children: List[ChildResponse]
    total_count: int


class GrowthRecordCreate(BaseModel):
    """Schema for creating a growth record."""
    age_months: int = Field(..., ge=0, le=60, description="Child's age in months")
    weight_kg: float = Field(..., gt=0, le=50, description="Weight in kilograms")
    height_cm: float = Field(..., gt=0, le=150, description="Height in centimeters") 
    muac_cm: Optional[float] = Field(None, gt=0, le=30, description="Mid-upper arm circumference in cm")
    diet_diversity_score: int = Field(..., ge=0, le=10, description="Dietary diversity score")
    recent_infection: bool = Field(default=False, description="Recent infection status")
    
    # Optional manual Z-scores and percentiles
    weight_for_age_zscore: Optional[float] = Field(None, ge=-5, le=5)
    height_for_age_zscore: Optional[float] = Field(None, ge=-5, le=5)
    bmi_for_age_zscore: Optional[float] = Field(None, ge=-5, le=5)
    muac_for_age_zscore: Optional[float] = Field(None, ge=-5, le=5)
    weight_for_age_percentile: Optional[float] = Field(None, ge=0, le=100)
    height_for_age_percentile: Optional[float] = Field(None, ge=0, le=100)
    bmi_for_age_percentile: Optional[float] = Field(None, ge=0, le=100)
    muac_for_age_percentile: Optional[float] = Field(None, ge=0, le=100)


class PredictionResult(BaseModel):
    """Schema for prediction results."""
    malnutrition_status: str
    developmental_risk: str
    confidence_score: Optional[float] = None
    timestamp: datetime


class GrowthRecordResponse(BaseModel):
    """Schema for growth record response with predictions."""
    model_config = ConfigDict(from_attributes=True)
    
    record_id: UUID
    child_id: UUID
    age_months: int
    weight_kg: float
    height_cm: float
    muac_cm: Optional[float]
    bmi: Optional[float]
    diet_diversity_score: int
    recent_infection: bool
    z_scores_percentiles: Optional[Dict[str, Any]]
    prediction_results: Optional[Dict[str, Any]]
    recorded_at: datetime


class GrowthPredictionResponse(BaseModel):
    """Schema for growth prediction API response."""
    malnutrition_status: str = Field(..., description="Predicted malnutrition status")
    developmental_risk: str = Field(..., description="Predicted developmental risk level")
    recommendations: List[str] = Field(..., description="Personalized recommendations")
    record_id: UUID = Field(..., description="Created growth record ID")
    bmi_calculated: Optional[float] = Field(None, description="Calculated BMI")


class ChildGrowthHistory(BaseModel):
    """Schema for child's growth history."""
    child_info: ChildResponse
    growth_records: List[GrowthRecordResponse]
    total_records: int
    latest_prediction: Optional[Dict[str, Any]]


class GrowthTrend(BaseModel):
    """Schema for growth trend analysis."""
    child_id: UUID
    measurements: List[Dict[str, Any]]
    trends: Dict[str, str]  # e.g., {"weight": "improving", "height": "stable"}
    alerts: List[str]  # Any concerning patterns
