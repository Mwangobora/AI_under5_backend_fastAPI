import joblib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class MLModels:
    """ML model loader and predictor service."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.chatbot_model: Optional[Any] = None
        self.prediction_model: Optional[Any] = None
        self.recommendation_model: Optional[Any] = None
        
        # Mapping dictionaries for predictions
        self.malnutrition_labels = {
            0: "Normal",
            1: "Stunting", 
            2: "Underweight",
            3: "Overweight",
            4: "Severe"
        }
        
        self.risk_labels = {
            0: "No Risk",
            1: "At Risk", 
            2: "High Risk"
        }
    
    async def load_models(self) -> None:
        """Load all ML models at startup."""
        try:
            # Load chatbot model
            chatbot_path = self.models_dir / "chatbot_model.pkl"
            if chatbot_path.exists():
                self.chatbot_model = joblib.load(chatbot_path)
                logger.info("Chatbot model loaded successfully")
            else:
                logger.warning(f"Chatbot model not found at {chatbot_path}")
            
            # Load prediction model
            prediction_path = self.models_dir / "prediction_model.pkl"
            if prediction_path.exists():
                self.prediction_model = joblib.load(prediction_path)
                logger.info("Prediction model loaded successfully")
            else:
                logger.warning(f"Prediction model not found at {prediction_path}")
            
            # Load recommendation model
            recommendation_path = self.models_dir / "recommendation_model.pkl"
            if recommendation_path.exists():
                self.recommendation_model = joblib.load(recommendation_path)
                logger.info("Recommendation model loaded successfully")
            else:
                logger.warning(f"Recommendation model not found at {recommendation_path}")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def get_chatbot_answer(self, question: str) -> str:
        """Get answer from chatbot model."""
        if self.chatbot_model is None:
            # Fallback responses for when model is not available
            return self._get_fallback_chatbot_answer(question)
        
        try:
            # If the model has a predict method
            if hasattr(self.chatbot_model, 'predict'):
                answer = self.chatbot_model.predict([question])[0]
            # If the model has a get_answer method
            elif hasattr(self.chatbot_model, 'get_answer'):
                answer = self.chatbot_model.get_answer(question)
            else:
                # Try to call the model directly
                answer = self.chatbot_model(question)
            
            return str(answer)
            
        except Exception as e:
            logger.error(f"Error in chatbot prediction: {e}")
            return self._get_fallback_chatbot_answer(question)
    
    def predict_malnutrition_risk(self, features: Dict[str, Any]) -> Dict[str, str]:
        """Predict malnutrition status and developmental risk."""
        if self.prediction_model is None:
            # Fallback prediction
            return self._get_fallback_prediction(features)
        
        try:
            # Prepare features for prediction
            feature_vector = self._prepare_prediction_features(features)
            
            # Make prediction
            if hasattr(self.prediction_model, 'predict'):
                predictions = self.prediction_model.predict([feature_vector])
            else:
                predictions = self.prediction_model([feature_vector])
            
            # Handle different prediction formats
            if isinstance(predictions, (list, tuple)) and len(predictions) >= 2:
                malnutrition_pred = predictions[0]
                risk_pred = predictions[1]
            elif hasattr(predictions, 'shape') and len(predictions.shape) > 1:
                malnutrition_pred = predictions[0][0]
                risk_pred = predictions[0][1] if predictions.shape[1] > 1 else 0
            else:
                # Single prediction - use heuristics to determine both
                pred_value = predictions[0] if isinstance(predictions, (list, np.ndarray)) else predictions
                malnutrition_pred = pred_value
                risk_pred = self._infer_risk_from_malnutrition(pred_value)
            
            # Map predictions to labels
            malnutrition_status = self.malnutrition_labels.get(int(malnutrition_pred), "Normal")
            developmental_risk = self.risk_labels.get(int(risk_pred), "No Risk")
            
            return {
                "malnutrition_status": malnutrition_status,
                "developmental_risk": developmental_risk
            }
            
        except Exception as e:
            logger.error(f"Error in malnutrition prediction: {e}")
            return self._get_fallback_prediction(features)
    
    def get_recommendation(self, malnutrition_status: str, developmental_risk: str) -> str:
        """Get nutrition and developmental recommendations."""
        if self.recommendation_model is None:
            return self._get_fallback_recommendation(malnutrition_status, developmental_risk)
        
        try:
            # Prepare input for recommendation model
            input_data = self._prepare_recommendation_input(malnutrition_status, developmental_risk)
            
            # Make recommendation
            if hasattr(self.recommendation_model, 'predict'):
                recommendation = self.recommendation_model.predict([input_data])[0]
            elif hasattr(self.recommendation_model, 'get_recommendation'):
                recommendation = self.recommendation_model.get_recommendation(input_data)
            else:
                recommendation = self.recommendation_model(input_data)
            
            return str(recommendation)
            
        except Exception as e:
            logger.error(f"Error in recommendation generation: {e}")
            return self._get_fallback_recommendation(malnutrition_status, developmental_risk)
    
    def _prepare_prediction_features(self, features: Dict[str, Any]) -> list:
        """Prepare features for prediction model."""
        # Convert categorical features
        sex_encoded = 1 if features["Sex"] == "Male" else 0
        infection_encoded = 1 if features["Recent_Infection"] == "Yes" else 0
        
        # Create feature vector in expected order
        feature_vector = [
            features["Age_Months"],
            sex_encoded,
            features["Weight_kg"],
            features["Height_cm"],
            features["HeadCircumference_cm"],
            features["MUAC_cm"],
            features["BMI"],
            features["Diet_Diversity_Score"],
            infection_encoded,
            features["Weight_for_Age_ZScore"],
            features["Height_for_Age_ZScore"],
            features["BMI_for_Age_ZScore"],
            features["MUAC_for_Age_ZScore"],
            features["Weight_for_Age_Percentile"],
            features["Height_for_Age_Percentile"],
            features["BMI_for_Age_Percentile"],
            features["MUAC_for_Age_Percentile"]
        ]
        
        return feature_vector
    
    def _prepare_recommendation_input(self, malnutrition_status: str, developmental_risk: str) -> list:
        """Prepare input for recommendation model."""
        # Encode categorical inputs
        malnutrition_encoded = {v: k for k, v in self.malnutrition_labels.items()}[malnutrition_status]
        risk_encoded = {v: k for k, v in self.risk_labels.items()}[developmental_risk]
        
        return [malnutrition_encoded, risk_encoded]
    
    def _infer_risk_from_malnutrition(self, malnutrition_pred: int) -> int:
        """Infer developmental risk from malnutrition status."""
        if malnutrition_pred in [4]:  # Severe
            return 2  # High Risk
        elif malnutrition_pred in [1, 2, 3]:  # Stunting, Underweight, Overweight
            return 1  # At Risk
        else:  # Normal
            return 0  # No Risk
    
    def _get_fallback_chatbot_answer(self, question: str) -> str:
        """Fallback answers when chatbot model is unavailable."""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["feed", "food", "eat", "nutrition"]):
            return ("For healthy growth, feed your child a variety of foods including fruits, vegetables, grains, proteins like beans or eggs, and dairy products. "
                   "Ensure meals are regular and age-appropriate. Breastfeeding is important for babies under 2 years. "
                   "Consult your healthcare provider for specific dietary guidance.")
        
        elif any(word in question_lower for word in ["growth", "develop", "milestone"]):
            return ("Each child develops at their own pace, but regular check-ups are important. "
                   "Ensure good nutrition, adequate sleep, and engage in age-appropriate play activities. "
                   "Monitor key milestones and consult your healthcare provider if you have concerns about your child's development.")
        
        elif any(word in question_lower for word in ["weight", "height", "size"]):
            return ("Regular growth monitoring is essential for children. Maintain growth charts and visit your healthcare provider regularly. "
                   "Focus on balanced nutrition, physical activity appropriate for the child's age, and adequate rest. "
                   "Contact your healthcare provider if growth patterns seem concerning.")
        
        else:
            return ("For the best care of your child, ensure proper nutrition with diverse foods, regular medical check-ups, and age-appropriate activities. "
                   "Each child is unique, so consult with your healthcare provider for personalized advice about your child's health and development. "
                   "Maintain vaccination schedules and seek professional help when needed.")
    
    def _get_fallback_prediction(self, features: Dict[str, Any]) -> Dict[str, str]:
        """Fallback prediction based on simple rules."""
        bmi = features.get("BMI", 16)
        height_zscore = features.get("Height_for_Age_ZScore", 0)
        weight_zscore = features.get("Weight_for_Age_ZScore", 0)
        
        # Simple rule-based classification
        if height_zscore < -2:
            malnutrition_status = "Stunting"
        elif weight_zscore < -2:
            malnutrition_status = "Underweight"
        elif bmi > 25:
            malnutrition_status = "Overweight"
        elif weight_zscore < -3 or height_zscore < -3:
            malnutrition_status = "Severe"
        else:
            malnutrition_status = "Normal"
        
        # Determine risk based on status
        if malnutrition_status in ["Severe"]:
            developmental_risk = "High Risk"
        elif malnutrition_status in ["Stunting", "Underweight", "Overweight"]:
            developmental_risk = "At Risk"
        else:
            developmental_risk = "No Risk"
        
        return {
            "malnutrition_status": malnutrition_status,
            "developmental_risk": developmental_risk
        }
    
    def _get_fallback_recommendation(self, malnutrition_status: str, developmental_risk: str) -> str:
        """Fallback recommendations based on status."""
        recommendations = {
            ("Normal", "No Risk"): 
                "Your child is growing well! Continue providing balanced meals with fruits, vegetables, grains, and proteins. "
                "Keep regular meal times and ensure adequate physical activity. Visit the clinic for routine check-ups to maintain healthy growth.",
            
            ("Stunting", "At Risk"):
                "Your child shows signs of stunting which affects height growth. Provide protein-rich foods like beans, groundnuts, eggs, milk, and fish. "
                "Include iron-rich foods and fruits for vitamins. Please visit the clinic immediately for growth monitoring and nutritional counseling.",
            
            ("Stunting", "High Risk"):
                "Your child has severe stunting requiring urgent attention. Increase protein intake with beans, meat, eggs, and milk daily. "
                "Add nutrient-dense foods and consider therapeutic feeding programs. Visit the clinic urgently for specialized care and monitoring.",
            
            ("Underweight", "At Risk"):
                "Your child is underweight and needs more nutritious food. Add calorie-dense foods like groundnuts, avocados, and cooking oil to meals. "
                "Provide frequent small meals with proteins and healthy fats. Please visit the clinic for growth assessment and feeding guidance.",
            
            ("Underweight", "High Risk"):
                "Your child is severely underweight and needs immediate intervention. Increase meal frequency and add high-energy foods daily. "
                "Include therapeutic foods if available and ensure treatment for any infections. Visit the health facility urgently for specialized care.",
            
            ("Overweight", "At Risk"):
                "Your child is overweight which can affect healthy development. Reduce sugary foods and increase fruits and vegetables. "
                "Encourage active play and limit sedentary time. Visit the clinic for proper assessment and guidance on healthy eating habits.",
            
            ("Overweight", "High Risk"):
                "Your child has significant overweight requiring careful management. Focus on nutritious, balanced meals without excess sugars or fats. "
                "Increase physical activity through play and sports. Please visit the clinic for comprehensive evaluation and weight management plan.",
            
            ("Severe", "High Risk"):
                "Your child has severe malnutrition requiring immediate medical attention. This is a serious condition that needs urgent treatment. "
                "Visit the hospital or clinic immediately for emergency care. Follow all medical advice and therapeutic feeding protocols strictly."
        }
        
        key = (malnutrition_status, developmental_risk)
        return recommendations.get(key, 
            "Based on your child's nutritional status, please provide balanced meals with proteins, fruits, and vegetables. "
            "Visit your local clinic for proper assessment and personalized guidance on your child's nutrition and growth.")


# Global instance
ml_models = MLModels()
