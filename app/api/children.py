from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.database import get_async_session
from app.schemas.children import (
    ChildRegister, ChildResponse, ChildListResponse,
    GrowthRecordCreate, GrowthPredictionResponse, ChildGrowthHistory,
    GrowthRecordResponse, GrowthTrend
)
from app.crud.children import (
    create_child, get_children_by_parent, get_child_by_id,
    create_growth_record, update_growth_record_predictions,
    get_child_growth_history, analyze_growth_trends
)
from app.api.users import get_current_user
from app.ml.model_loader import ml_models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/children", tags=["Child Management"])


@router.post("/register", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def register_child(
    child_data: ChildRegister,
    current_user=Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> ChildResponse:
    """Register a new child for the current user."""
    try:
        logger.info(f"Registering child for user {current_user.id}: {child_data.name}")
        
        # Create child record
        child = await create_child(db, child_data, current_user.id)
        
        # Convert sex enum to string for response
        child_response = ChildResponse(
            child_id=child.child_id,
            name=child.name,
            sex=child.sex.value,
            birth_date=child.birth_date,
            created_at=child.created_at
        )
        
        logger.info(f"Child registered successfully: {child.child_id}")
        return child_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering child for user {current_user.id}: {e}")
        error_msg = "Imeshindwa kusajili mtoto" if current_user.language == "swahili" else "Failed to register child"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("", response_model=ChildListResponse)
async def get_user_children(
    current_user=Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> ChildListResponse:
    """Get all children for the current user."""
    try:
        logger.info(f"Fetching children for user {current_user.id}")
        
        children = await get_children_by_parent(db, current_user.id)
        
        # Convert children to response format
        child_responses = [
            ChildResponse(
                child_id=child.child_id,
                name=child.name,
                sex=child.sex.value,
                birth_date=child.birth_date,
                created_at=child.created_at
            )
            for child in children
        ]
        
        return ChildListResponse(
            children=child_responses,
            total_count=len(child_responses)
        )
        
    except Exception as e:
        logger.error(f"Error fetching children for user {current_user.id}: {e}")
        error_msg = "Imeshindwa kupata watoto" if current_user.language == "swahili" else "Failed to fetch children"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.post("/{child_id}/records", response_model=GrowthPredictionResponse)
async def create_child_growth_record(
    child_id: UUID,
    record_data: GrowthRecordCreate,
    current_user=Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> GrowthPredictionResponse:
    """Create a growth record and run predictions for a child."""
    try:
        logger.info(f"Creating growth record for child {child_id}, user {current_user.id}")
        
        # Create the growth record
        growth_record = await create_growth_record(db, child_id, record_data, current_user.id)
        
        # Prepare data for ML prediction
        child = await get_child_by_id(db, child_id, current_user.id)
        
        # Prepare prediction features
        prediction_features = {
            "Age_Months": record_data.age_months,
            "Sex": child.sex.value,
            "Weight_kg": record_data.weight_kg,
            "Height_cm": record_data.height_cm,
            "HeadCircumference_cm": 45.0,  # Default value if not provided
            "MUAC_cm": record_data.muac_cm or 14.0,
            "BMI": growth_record.bmi,
            "Diet_Diversity_Score": record_data.diet_diversity_score,
            "Recent_Infection": "Yes" if record_data.recent_infection else "No",
            "Weight_for_Age_ZScore": record_data.weight_for_age_zscore or 0.0,
            "Height_for_Age_ZScore": record_data.height_for_age_zscore or 0.0,
            "BMI_for_Age_ZScore": record_data.bmi_for_age_zscore or 0.0,
            "MUAC_for_Age_ZScore": record_data.muac_for_age_zscore or 0.0,
            "Weight_for_Age_Percentile": record_data.weight_for_age_percentile or 50.0,
            "Height_for_Age_Percentile": record_data.height_for_age_percentile or 50.0,
            "BMI_for_Age_Percentile": record_data.bmi_for_age_percentile or 50.0,
            "MUAC_for_Age_Percentile": record_data.muac_for_age_percentile or 50.0
        }
        
        # Run ML prediction (English-trained model)
        prediction_result = ml_models.predict_malnutrition_risk(prediction_features)
        
        # Get recommendations
        recommendations_text = ml_models.get_recommendation(
            prediction_result["malnutrition_status"],
            prediction_result["developmental_risk"],
            current_user.language
        )
        
        # Parse recommendations into list
        recommendations = [rec.strip() for rec in recommendations_text.split('.') if rec.strip()]
        
        # Update growth record with predictions
        prediction_data = {
            "malnutrition_status": prediction_result["malnutrition_status"],
            "developmental_risk": prediction_result["developmental_risk"]
        }
        
        await update_growth_record_predictions(db, growth_record.record_id, prediction_data)
        
        logger.info(f"Growth record created and predictions saved for child {child_id}")
        
        return GrowthPredictionResponse(
            malnutrition_status=prediction_result["malnutrition_status"],
            developmental_risk=prediction_result["developmental_risk"],
            recommendations=recommendations,
            record_id=growth_record.record_id,
            bmi_calculated=growth_record.bmi
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating growth record for child {child_id}: {e}")
        error_msg = "Imeshindwa kutengeneza rekodi ya ukuaji" if current_user.language == "swahili" else "Failed to create growth record"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/{child_id}/history", response_model=ChildGrowthHistory)
async def get_child_history(
    child_id: UUID,
    current_user=Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> ChildGrowthHistory:
    """Get growth history for a child."""
    try:
        logger.info(f"Fetching growth history for child {child_id}, user {current_user.id}")
        
        # Get child info
        child = await get_child_by_id(db, child_id, current_user.id)
        if not child:
            error_msg = "Mtoto hajapatikana" if current_user.language == "swahili" else "Child not found"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # Get growth records
        growth_records = await get_child_growth_history(db, child_id, current_user.id)
        
        # Convert to response format
        child_info = ChildResponse(
            child_id=child.child_id,
            name=child.name,
            sex=child.sex.value,
            birth_date=child.birth_date,
            created_at=child.created_at
        )
        
        record_responses = [
            GrowthRecordResponse(
                record_id=record.record_id,
                child_id=record.child_id,
                age_months=record.age_months,
                weight_kg=record.weight_kg,
                height_cm=record.height_cm,
                muac_cm=record.muac_cm,
                bmi=record.bmi,
                diet_diversity_score=record.diet_diversity_score,
                recent_infection=record.recent_infection,
                z_scores_percentiles=record.z_scores_percentiles,
                prediction_results=record.prediction_results,
                recorded_at=record.recorded_at
            )
            for record in growth_records
        ]
        
        # Get latest prediction
        latest_prediction = None
        if growth_records and growth_records[0].prediction_results:
            latest_prediction = growth_records[0].prediction_results
        
        return ChildGrowthHistory(
            child_info=child_info,
            growth_records=record_responses,
            total_records=len(record_responses),
            latest_prediction=latest_prediction
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching child history {child_id}: {e}")
        error_msg = "Imeshindwa kupata historia ya mtoto" if current_user.language == "swahili" else "Failed to fetch child history"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/{child_id}/trends", response_model=GrowthTrend)
async def get_child_growth_trends(
    child_id: UUID,
    current_user=Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_async_session)]
) -> GrowthTrend:
    """Get growth trend analysis for a child."""
    try:
        logger.info(f"Analyzing growth trends for child {child_id}, user {current_user.id}")
        
        # Analyze trends
        trend_analysis = await analyze_growth_trends(db, child_id, current_user.id)
        
        # Get recent measurements for trend visualization
        recent_records = await get_child_growth_history(db, child_id, current_user.id, limit=10)
        
        measurements = [
            {
                "age_months": record.age_months,
                "weight_kg": record.weight_kg,
                "height_cm": record.height_cm,
                "bmi": record.bmi,
                "recorded_at": record.recorded_at.isoformat(),
                "prediction": record.prediction_results
            }
            for record in sorted(recent_records, key=lambda x: x.age_months)
        ]
        
        # Translate alerts to user's language
        alerts = trend_analysis.get("alerts", [])
        if current_user.language == "swahili":
            swahili_alerts = []
            for alert in alerts:
                if "Weight showing decreasing trend" in alert:
                    swahili_alerts.append("Uzito unashuka - hali ya wasiwasi")
                elif "Height showing concerning pattern" in alert:
                    swahili_alerts.append("Urefu una mfumo wa wasiwasi")
                elif "Concerning nutritional status" in alert:
                    swahili_alerts.append(f"Hali ya lishe ya wasiwasi: {alert.split(': ')[1]}")
                else:
                    swahili_alerts.append(alert)
            alerts = swahili_alerts
        
        return GrowthTrend(
            child_id=child_id,
            measurements=measurements,
            trends=trend_analysis.get("trends", {}),
            alerts=alerts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trends for child {child_id}: {e}")
        error_msg = "Imeshindwa kuchambua mienendo ya ukuaji" if current_user.language == "swahili" else "Failed to analyze growth trends"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
