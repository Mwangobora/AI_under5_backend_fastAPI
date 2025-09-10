# ML Models Directory

Place your trained ML model files (.pkl) in this directory:

## Required Model Files

1. **chatbot_model.pkl** - Conversational Q&A model
   - Should have a `.predict(question)` or `.get_answer(question)` method
   - Expected to return multi-sentence answers about child nutrition/health

2. **prediction_model.pkl** - Child growth & nutrition prediction model
   - Should have a `.predict(features)` method
   - Expected to return predictions that can be mapped to:
     - Malnutrition status: 0=Normal, 1=Stunting, 2=Underweight, 3=Overweight, 4=Severe
     - Developmental risk: 0=No Risk, 1=At Risk, 2=High Risk

3. **recommendation_model.pkl** - Nutrition & developmental advice model
   - Should have a `.predict(encoded_status)` method
   - Expected to return detailed recommendations in simple language

## Model Input/Output Format

### Chatbot Model
```python
# Input: string (question)
question = "What should I feed my 2-year-old?"

# Output: string (multi-sentence answer)
answer = model.predict([question])[0]
```

### Prediction Model
```python
# Input: list of 17 features
features = [age_months, sex_encoded, weight_kg, height_cm, head_circ_cm, 
           muac_cm, bmi, diet_score, infection_encoded, weight_zscore, 
           height_zscore, bmi_zscore, muac_zscore, weight_percentile, 
           height_percentile, bmi_percentile, muac_percentile]

# Output: predictions (single or multiple outputs)
predictions = model.predict([features])
```

### Recommendation Model
```python
# Input: list of encoded status [malnutrition_code, risk_code]
input_data = [1, 2]  # Stunting, High Risk

# Output: string (recommendation text)
recommendation = model.predict([input_data])[0]
```

## Fallback System

The application includes fallback responses when models are not available:
- Rule-based predictions using Z-scores and BMI thresholds
- Pre-defined recommendation templates
- Contextual chatbot responses based on question keywords

## Loading Models

Models are loaded at application startup. If a model file is missing, the application will:
1. Log a warning message
2. Use fallback logic for that specific model
3. Continue running normally

Place your trained model files here and restart the application to use them.
