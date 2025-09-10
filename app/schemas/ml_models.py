from pydantic import BaseModel, Field
from typing import Literal, Optional


class ChatbotRequest(BaseModel):
    """Schema for chatbot question request."""
    question: str = Field(..., min_length=1, max_length=500, description="Question about child nutrition, health, development, or parenting")
    language: Optional[Literal["english", "swahili"]] = Field(default="english", description="Response language preference")


class ChatbotResponse(BaseModel):
    """Schema for chatbot response."""
    answer: str = Field(..., description="Detailed answer providing guidance for parents")


class PredictionRequest(BaseModel):
    """Schema for child growth and nutrition prediction request."""
    Age_Months: int = Field(..., ge=0, le=60, description="Child's age in months")
    Sex: Literal["Male", "Female"] = Field(..., description="Child's sex")
    Weight_kg: float = Field(..., ge=0, le=50, description="Child's weight in kilograms")
    Height_cm: float = Field(..., ge=0, le=150, description="Child's height in centimeters")
    HeadCircumference_cm: float = Field(..., ge=0, le=60, description="Head circumference in centimeters")
    MUAC_cm: float = Field(..., ge=0, le=30, description="Mid-upper arm circumference in centimeters")
    BMI: float = Field(..., ge=0, le=40, description="Body Mass Index")
    Diet_Diversity_Score: int = Field(..., ge=0, le=10, description="Dietary diversity score")
    Recent_Infection: Literal["Yes", "No"] = Field(..., description="Recent infection status")
    Weight_for_Age_ZScore: float = Field(..., ge=-5, le=5, description="Weight-for-age Z-score")
    Height_for_Age_ZScore: float = Field(..., ge=-5, le=5, description="Height-for-age Z-score")
    BMI_for_Age_ZScore: float = Field(..., ge=-5, le=5, description="BMI-for-age Z-score")
    MUAC_for_Age_ZScore: float = Field(..., ge=-5, le=5, description="MUAC-for-age Z-score")
    Weight_for_Age_Percentile: float = Field(..., ge=0, le=100, description="Weight-for-age percentile")
    Height_for_Age_Percentile: float = Field(..., ge=0, le=100, description="Height-for-age percentile")
    BMI_for_Age_Percentile: float = Field(..., ge=0, le=100, description="BMI-for-age percentile")
    MUAC_for_Age_Percentile: float = Field(..., ge=0, le=100, description="MUAC-for-age percentile")


class PredictionResponse(BaseModel):
    """Schema for prediction response."""
    malnutrition_status: Literal["Normal", "Stunting", "Underweight", "Overweight", "Severe"] = Field(
        ..., description="Malnutrition classification"
    )
    developmental_risk: Literal["No Risk", "At Risk", "High Risk"] = Field(
        ..., description="Developmental risk assessment"
    )


class RecommendationRequest(BaseModel):
    """Schema for recommendation request."""
    malnutrition_status: Literal["Normal", "Stunting", "Underweight", "Overweight", "Severe"] = Field(
        ..., description="Malnutrition status from prediction"
    )
    developmental_risk: Literal["No Risk", "At Risk", "High Risk"] = Field(
        ..., description="Developmental risk from prediction"
    )
    language: Optional[Literal["english", "swahili"]] = Field(default="english", description="Response language preference")


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    recommendation: str = Field(..., description="Detailed nutrition and health recommendation in simple language")


class LanguagePreference(BaseModel):
    """Schema for user language preference."""
    language: Literal["english", "swahili"] = Field(..., description="Preferred language for responses")


class LanguageResponse(BaseModel):
    """Schema for language preference response."""
    language: str = Field(..., description="Current language preference")
    message: str = Field(..., description="Confirmation message")
