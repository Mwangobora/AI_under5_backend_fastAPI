from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.database import get_async_session
from app.schemas.ml_models import (
    ChatbotRequest, ChatbotResponse,
    PredictionRequest, PredictionResponse,
    RecommendationRequest, RecommendationResponse
)
from app.api.users import get_current_user
from app.ml.model_loader import ml_models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ML Predictions"])


@router.post("/chatbot", response_model=ChatbotResponse)
async def chatbot_question(
    request: ChatbotRequest,
    current_user=Depends(get_current_user)
) -> ChatbotResponse:
    """
    Get answers to child nutrition, health, development, and parenting questions.
    
    This endpoint provides conversational Q&A for parents seeking guidance
    about their child's nutrition, health, development, play activities,
    sleep, and general parenting advice.
    """
    try:
        logger.info(f"Chatbot question from user {current_user.id}: {request.question[:50]}...")
        
        # Use language from request or user's preference
        language = request.language or current_user.language
        
        # Get answer from chatbot model
        answer = ml_models.get_chatbot_answer(request.question, language)
        
        if not answer or len(answer.strip()) < 10:
            error_msg = "Imeshindwa kutoa jibu sahihi. Tafadhali jaribu tena." if language == "swahili" else "Unable to generate a proper response. Please try again."
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
        
        logger.info(f"Chatbot response generated for user {current_user.id} in {language}")
        return ChatbotResponse(answer=answer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chatbot error for user {current_user.id}: {e}")
        error_msg = "Kosa katika kuchakata swali lako. Tafadhali jaribu tena." if (request.language or current_user.language) == "swahili" else "Error processing your question. Please try again."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.post("/predict", response_model=PredictionResponse)
async def predict_malnutrition_risk(
    request: PredictionRequest,
    current_user=Depends(get_current_user)
) -> PredictionResponse:
    """
    Predict child malnutrition status and developmental risk.
    
    This endpoint analyzes child growth features to predict:
    - Malnutrition status (Normal, Stunting, Underweight, Overweight, Severe)
    - Developmental risk (No Risk, At Risk, High Risk)
    """
    try:
        logger.info(f"Prediction request from user {current_user.id} for {request.Age_Months} month old {request.Sex}")
        
        # Convert request to dictionary
        features = request.model_dump()
        
        # Validate critical features
        if request.Age_Months <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Age must be greater than 0 months"
            )
        
        if request.Weight_kg <= 0 or request.Height_cm <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight and height must be positive values"
            )
        
        # Get prediction from model
        prediction_result = ml_models.predict_malnutrition_risk(features)
        
        response = PredictionResponse(
            malnutrition_status=prediction_result["malnutrition_status"],
            developmental_risk=prediction_result["developmental_risk"]
        )
        
        logger.info(f"Prediction completed for user {current_user.id}: {response.malnutrition_status}, {response.developmental_risk}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing prediction. Please check your input data."
        )


@router.post("/recommend", response_model=RecommendationResponse)
async def get_nutrition_recommendation(
    request: RecommendationRequest,
    current_user=Depends(get_current_user)
) -> RecommendationResponse:
    """
    Get nutrition and developmental recommendations.
    
    This endpoint provides personalized nutrition and health recommendations
    based on the child's malnutrition status and developmental risk.
    """
    try:
        logger.info(f"Recommendation request from user {current_user.id}: {request.malnutrition_status}, {request.developmental_risk}")
        
        # Use language from request or user's preference
        language = request.language or current_user.language
        
        # Get recommendation from model
        recommendation = ml_models.get_recommendation(
            request.malnutrition_status,
            request.developmental_risk,
            language
        )
        
        if not recommendation or len(recommendation.strip()) < 20:
            error_msg = "Imeshindwa kutoa mapendekezo sahihi. Tafadhali jaribu tena." if language == "swahili" else "Unable to generate proper recommendations. Please try again."
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
        
        response = RecommendationResponse(recommendation=recommendation)
        
        logger.info(f"Recommendation completed for user {current_user.id} in {language}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error for user {current_user.id}: {e}")
        error_msg = "Kosa katika kutengeneza mapendekezo. Tafadhali jaribu tena." if (request.language or current_user.language) == "swahili" else "Error generating recommendations. Please try again."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


# Combined endpoint for predict + recommend workflow
@router.post("/analyze", response_model=dict)
async def analyze_child_nutrition(
    request: PredictionRequest,
    current_user=Depends(get_current_user)
) -> dict:
    """
    Complete nutritional analysis: prediction + recommendations.
    
    This endpoint combines prediction and recommendation in a single call
    for mobile apps that need both results together.
    """
    try:
        logger.info(f"Complete analysis request from user {current_user.id}")
        
        # Convert request to dictionary
        features = request.model_dump()
        
        # Validate critical features
        if request.Age_Months <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Age must be greater than 0 months"
            )
        
        if request.Weight_kg <= 0 or request.Height_cm <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight and height must be positive values"
            )
        
        # Get prediction
        prediction_result = ml_models.predict_malnutrition_risk(features)
        
        # Get recommendation based on prediction
        recommendation = ml_models.get_recommendation(
            prediction_result["malnutrition_status"],
            prediction_result["developmental_risk"],
            current_user.language
        )
        
        response = {
            "prediction": {
                "malnutrition_status": prediction_result["malnutrition_status"],
                "developmental_risk": prediction_result["developmental_risk"]
            },
            "recommendation": recommendation,
            "child_info": {
                "age_months": request.Age_Months,
                "sex": request.Sex,
                "weight_kg": request.Weight_kg,
                "height_cm": request.Height_cm
            }
        }
        
        logger.info(f"Complete analysis completed for user {current_user.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing nutritional analysis. Please check your input data."
        )
