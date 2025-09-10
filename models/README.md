# ML Models Directory

Place your trained ML model files (.pkl) in this directory:

## Required Model Files

1. **chatbot_model.pkl** - Conversational Q&A model (MULTILINGUAL)
   - Should have a `.predict(question)` or `.get_answer(question)` method
   - **FINE-TUNED FOR BOTH ENGLISH & SWAHILI**
   - Responds to language context prompts:
     - "Answer in English: [question]" → English response
     - "Jibu kwa Kiswahili: [question]" → Swahili response
   - Expected to return multi-sentence answers about child nutrition/health/parenting

2. **prediction_model.pkl** - Child growth & nutrition prediction model (ENGLISH)
   - Should have a `.predict(features)` method
   - **TRAINED WITH ENGLISH DATA**
   - Expected to return predictions that can be mapped to:
     - Malnutrition status: 0=Normal, 1=Stunting, 2=Underweight, 3=Overweight, 4=Severe
     - Developmental risk: 0=No Risk, 1=At Risk, 2=High Risk

3. **recommendation_model.pkl** - Nutrition & developmental advice model (ENGLISH)
   - Should have a `.predict(encoded_status)` method
   - **TRAINED WITH ENGLISH DATA**
   - Returns English recommendations (automatically translated to Swahili when needed)
   - Expected to return detailed recommendations in simple language

## Model Input/Output Format

### Chatbot Model (Multilingual)
```python
# English input
question_en = "Answer in English: What should I feed my 2-year-old?"
answer_en = model.predict([question_en])[0]

# Swahili input  
question_sw = "Jibu kwa Kiswahili: Nimpe nini mtoto wangu wa miaka 2?"
answer_sw = model.predict([question_sw])[0]

# The fine-tuned model automatically responds in the requested language
```

### Prediction Model (English-trained)
```python
# Input: list of 17 features
features = [age_months, sex_encoded, weight_kg, height_cm, head_circ_cm, 
           muac_cm, bmi, diet_score, infection_encoded, weight_zscore, 
           height_zscore, bmi_zscore, muac_zscore, weight_percentile, 
           height_percentile, bmi_percentile, muac_percentile]

# Output: numerical predictions (English labels applied later)
predictions = model.predict([features])
# Returns: [malnutrition_class, risk_class] as integers
```

### Recommendation Model (English-trained)
```python
# Input: list of encoded status [malnutrition_code, risk_code]
input_data = [1, 2]  # Stunting, High Risk

# Output: string (English recommendation text)
recommendation = model.predict([input_data])[0]
# Returns English text - automatically translated to Swahili when needed
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
