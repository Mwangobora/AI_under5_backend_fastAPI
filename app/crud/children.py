from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.models import Child, GrowthRecord, SexEnum
from app.schemas.children import ChildRegister, GrowthRecordCreate


async def create_child(db: AsyncSession, child_data: ChildRegister, parent_id: UUID) -> Child:
    """Create a new child record."""
    try:
        # Convert sex string to enum
        sex_enum = SexEnum.MALE if child_data.sex == "Male" else SexEnum.FEMALE
        
        db_child = Child(
            parent_id=parent_id,
            name=child_data.name,
            sex=sex_enum,
            birth_date=child_data.birth_date
        )
        
        db.add(db_child)
        await db.commit()
        await db.refresh(db_child)
        return db_child
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register child"
        )


async def get_children_by_parent(db: AsyncSession, parent_id: UUID) -> List[Child]:
    """Get all children for a parent."""
    result = await db.execute(
        select(Child).where(Child.parent_id == parent_id).order_by(Child.created_at.desc())
    )
    return result.scalars().all()


async def get_child_by_id(db: AsyncSession, child_id: UUID, parent_id: UUID) -> Optional[Child]:
    """Get a specific child by ID (ensuring it belongs to the parent)."""
    result = await db.execute(
        select(Child).where(
            and_(Child.child_id == child_id, Child.parent_id == parent_id)
        )
    )
    return result.scalar_one_or_none()


async def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate BMI from weight and height."""
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


async def calculate_age_months(birth_date: date, record_date: date = None) -> int:
    """Calculate age in months from birth date."""
    if record_date is None:
        record_date = date.today()
    
    age_years = record_date.year - birth_date.year
    age_months = record_date.month - birth_date.month
    
    if record_date.day < birth_date.day:
        age_months -= 1
    
    return (age_years * 12) + age_months


async def create_growth_record(
    db: AsyncSession, 
    child_id: UUID, 
    record_data: GrowthRecordCreate,
    parent_id: UUID
) -> GrowthRecord:
    """Create a new growth record for a child."""
    try:
        # Verify child belongs to parent
        child = await get_child_by_id(db, child_id, parent_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Calculate BMI
        calculated_bmi = await calculate_bmi(record_data.weight_kg, record_data.height_cm)
        
        # Prepare Z-scores and percentiles if provided
        z_scores_percentiles = {}
        if record_data.weight_for_age_zscore is not None:
            z_scores_percentiles["weight_for_age_zscore"] = record_data.weight_for_age_zscore
        if record_data.height_for_age_zscore is not None:
            z_scores_percentiles["height_for_age_zscore"] = record_data.height_for_age_zscore
        if record_data.bmi_for_age_zscore is not None:
            z_scores_percentiles["bmi_for_age_zscore"] = record_data.bmi_for_age_zscore
        if record_data.muac_for_age_zscore is not None:
            z_scores_percentiles["muac_for_age_zscore"] = record_data.muac_for_age_zscore
        if record_data.weight_for_age_percentile is not None:
            z_scores_percentiles["weight_for_age_percentile"] = record_data.weight_for_age_percentile
        if record_data.height_for_age_percentile is not None:
            z_scores_percentiles["height_for_age_percentile"] = record_data.height_for_age_percentile
        if record_data.bmi_for_age_percentile is not None:
            z_scores_percentiles["bmi_for_age_percentile"] = record_data.bmi_for_age_percentile
        if record_data.muac_for_age_percentile is not None:
            z_scores_percentiles["muac_for_age_percentile"] = record_data.muac_for_age_percentile
        
        # Create growth record
        db_record = GrowthRecord(
            child_id=child_id,
            age_months=record_data.age_months,
            weight_kg=record_data.weight_kg,
            height_cm=record_data.height_cm,
            muac_cm=record_data.muac_cm,
            bmi=calculated_bmi,
            diet_diversity_score=record_data.diet_diversity_score,
            recent_infection=record_data.recent_infection,
            z_scores_percentiles=z_scores_percentiles if z_scores_percentiles else None
        )
        
        db.add(db_record)
        await db.commit()
        await db.refresh(db_record)
        return db_record
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create growth record"
        )


async def update_growth_record_predictions(
    db: AsyncSession,
    record_id: UUID,
    predictions: Dict[str, Any]
) -> bool:
    """Update growth record with prediction results."""
    try:
        result = await db.execute(
            select(GrowthRecord).where(GrowthRecord.record_id == record_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            return False
        
        # Add timestamp to predictions
        predictions["timestamp"] = datetime.utcnow().isoformat()
        record.prediction_results = predictions
        
        await db.commit()
        return True
        
    except Exception:
        await db.rollback()
        return False


async def get_child_growth_history(
    db: AsyncSession, 
    child_id: UUID, 
    parent_id: UUID,
    limit: Optional[int] = None
) -> List[GrowthRecord]:
    """Get growth history for a child."""
    # Verify child belongs to parent
    child = await get_child_by_id(db, child_id, parent_id)
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    query = select(GrowthRecord).where(
        GrowthRecord.child_id == child_id
    ).order_by(desc(GrowthRecord.recorded_at))
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_latest_growth_record(
    db: AsyncSession,
    child_id: UUID,
    parent_id: UUID
) -> Optional[GrowthRecord]:
    """Get the latest growth record for a child."""
    records = await get_child_growth_history(db, child_id, parent_id, limit=1)
    return records[0] if records else None


async def analyze_growth_trends(
    db: AsyncSession,
    child_id: UUID,
    parent_id: UUID
) -> Dict[str, Any]:
    """Analyze growth trends for a child."""
    records = await get_child_growth_history(db, child_id, parent_id, limit=5)
    
    if len(records) < 2:
        return {"trends": {}, "alerts": []}
    
    # Sort by age (oldest first for trend analysis)
    records = sorted(records, key=lambda x: x.age_months)
    
    trends = {}
    alerts = []
    
    # Analyze weight trend
    weights = [r.weight_kg for r in records]
    if len(weights) >= 2:
        if weights[-1] > weights[0]:
            trends["weight"] = "increasing"
        elif weights[-1] < weights[0]:
            trends["weight"] = "decreasing"
            alerts.append("Weight showing decreasing trend")
        else:
            trends["weight"] = "stable"
    
    # Analyze height trend
    heights = [r.height_cm for r in records]
    if len(heights) >= 2:
        if heights[-1] > heights[0]:
            trends["height"] = "increasing"
        elif heights[-1] < heights[0]:
            trends["height"] = "decreasing"
            alerts.append("Height showing concerning pattern")
        else:
            trends["height"] = "stable"
    
    # Check for malnutrition alerts from recent predictions
    recent_predictions = [r.prediction_results for r in records[-3:] if r.prediction_results]
    severe_statuses = ["Severe", "Stunting", "Underweight"]
    
    for pred in recent_predictions:
        if pred and pred.get("malnutrition_status") in severe_statuses:
            alerts.append(f"Concerning nutritional status: {pred.get('malnutrition_status')}")
            break
    
    return {
        "trends": trends,
        "alerts": alerts,
        "total_records": len(records)
    }
