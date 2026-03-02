import json
import re
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env for local development
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

# If not found in environment, try Streamlit secrets (for cloud deployment)
if not API_KEY:
    try:
        import streamlit as st
        API_KEY = st.secrets.get("GOOGLE_API_KEY", None)
    except Exception:
        pass

if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found. Add it to Streamlit Cloud secrets or your .env file.")

# Configure Gemini
genai.configure(api_key=API_KEY)

# Use stable model
model = genai.GenerativeModel("models/gemini-2.5-flash")


def validate_price_with_ai(district, base_price, soil_data, year, user_inputs):


    prompt = f"""
You are an expert Agricultural Land Valuer and Agronomist in India.

**Goal**: Revalidate the machine learning predicted price based on real-world factors and analyze land suitability.

**Context**:
- District: {district}
- Year: {year}
- ML Model Base Price: ₹{base_price:,.0f} per acre

**Real-World Factors (User Input)**:
- Land Size: {user_inputs.get('land_size_acres')} acres
- Distance to Road: {user_inputs.get('distance_to_road')}
- Water Source: {user_inputs.get('water_source')}
- Land Type: {user_inputs.get('land_type')}
- Government Benefits (MSP): {user_inputs.get('msp_support')}
- Infrastructure Development: {', '.join(user_inputs.get('infra_developments', []))}
- Local Demand: {user_inputs.get('local_demand')}
- Plot Specifics: {', '.join(user_inputs.get('plot_specifics', []))}

**Soil Nutrients**:
- Zinc: {soil_data['Zn_%']}%
- Iron: {soil_data['Fe_%']}%
- Copper: {soil_data['Cu_%']}%
- Manganese: {soil_data['Mn_%']}%
- Boron: {soil_data['B_%']}%
- Sulphur: {soil_data['S_%']}%

**Instructions**:
1. **Price Revalidation**: Start with the 'ML Model Base Price'. Apply premiums or discounts based on the 'Real-World Factors'. 
   - **Size Impact**: Larger plots (e.g., >10 acres) often have a lower per-acre rate (volume discount) compared to small plots.
   - **Infrastructure**: Proximate upcoming projects (Highways, SEZs) should significantly increase value.
   - **Policy**: Availability of MSP support adds income stability -> premium.
   - **General**: Near highway (+), Good water (+), Litigation (-), Irregular shape (-).
   - Be conservative and realistic.

2. **Land Suitability**: Analyze the 'Soil Nutrients'.
   - Determine if it's best for 'Agriculture' or 'Non-Agriculture/Building'.
   - If Agriculture, recommend 3-4 suitable crops based on these specific micronutrient levels.
   - Give a suitability score (0-100).

3. **Profit Potential**:
   - Calculate a score out of 10 by evaluating: (Price Growth + Soil Quality + Location + Irrigation + Market Demand). Rate each factor up to 2 points.
   - Assign a descriptive label like "High Growth Potential", "Moderate Potential", etc.
   - Determine the recommendation: return exactly one of "🟢 Good to Buy", "🟡 Hold", or "🔴 Sell / Avoid" based on the score (e.g., > 7 for Good, 4-7 for Hold, < 4 for Sell).

4. **Target Audience**:
   - Determine if this land is better for "Farmers" (focused on yields, soil, water) or "Urban Investors/People" (focused on growth, infrastructure, location). 
   - Provide a short reason.

5. **5-Year ROI Projection**:
   - Estimate the expected cumulative Return on Investment (ROI) over the next 5 years as a percentage. 
   - Consider industrial growth, urban sprawl, market trends in {district}, and soil appreciation.
   - Return a single number (e.g., 45.5 for 45.5%).

**Output Format**:
Return ONLY a valid JSON object. Do not use Markdown backticks.
{{
    "final_price": <number, the new calculated price>,
    "price_difference_reasoning": "<short explanation of why price changed>",
    "suitability": {{
        "type": "<'Agriculture' or 'Non-Agriculture'>",
        "score": <number 0-100>,
        "crops": ["<crop1>", "<crop2>", "<crop3>"],
        "analysis": "<short analysis of soil quality and what can be improved>"
    }},
    "profit_potential": {{
        "score": <number 0-10>,
        "label": "<e.g. 'High Growth Potential'>",
        "recommendation": "<'🟢 Good to Buy', '🟡 Hold', or '🔴 Sell / Avoid'>"
    }},
    "target_audience": {{
        "suitable_for": "<'Farmers', 'Urban Investors', or 'Both'>",
        "reason": "<short explanation>"
    }},
    "roi_5yr": <number, percentage e.g. 45.5>
}}
"""

    try:
        response = model.generate_content(prompt)
        text_output = response.text
        
        # Clean potential markdown wrapping
        text_output = re.sub(r"```json", "", text_output)
        text_output = re.sub(r"```", "", text_output).strip()
        
        data = json.loads(text_output)
        return data

    except Exception as e:
        # Fallback in case of parsing error
        print(f"GenAI Error: {e}")
        return {
            "final_price": base_price,
            "price_difference_reasoning": f"AI validation failed: {str(e)}",
            "suitability": {
                "type": "Unknown",
                "score": 0,
                "crops": [],
                "analysis": "Could not analyze data."
            },
            "profit_potential": {
                "score": 0,
                "label": "Unknown",
                "recommendation": "🟡 Hold"
            },
            "target_audience": {
                "suitable_for": "Unknown",
                "reason": "AI validation failed."
            },
            "roi_5yr": 0
        }

def generate_advisory_report(district, year, predicted_price, soil_data, user_inputs):
    prompt = f"""
You are an expert Agricultural Land Investment Advisor in India.

Generate a professional LAND VALUATION REPORT for:

District: {district}
Year: {year}
Generated Price: ₹{predicted_price:,.0f} per acre

Soil Data:
Zinc: {soil_data['Zn_%']}%
Iron: {soil_data['Fe_%']}%
Copper: {soil_data['Cu_%']}%
Manganese: {soil_data['Mn_%']}%
Boron: {soil_data['B_%']}%
Sulphur: {soil_data['S_%']}%

Other Context:
- Proximity: {user_inputs.get('distance_to_road')}
- Resource: {user_inputs.get('water_source')}
- Infra: {', '.join(user_inputs.get('infra_developments', []))}

Structure your answer in this format:

1. **Executive Summary**: High-level overview of the property.
2. **Investment Rating**: (High / Medium / Low) with 1-sentence justification.
3. **Key Growth Drivers**: What will drive future price appreciation.
4. **Risk Factors**: Potential hurdles or environmental issues.
5. **Recommended Action**: (Buy / Hold / Sell) with short logic.
6. **Soil Improvement Plan**: Practical steps to enhance fertility.
7. **Recommended Crops**: Specific crops based on micro-nutrients.
8. **Government Policy & MSP impact**: How local/national policy affects this asset.
9. **Infrastructure & Development impact**: Analysis of roadmap projects.
10. **5-Year Future Price Outlook**: Predicted trend and final summary.

Write in simple Indian business language.
Make it like a professional advisory report. Use clear markdown formatting.
Do not use markdown backticks for the outer block, just return the text.
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"🚨 Advisory Report Generation Failed: {str(e)}"

def get_ai_advisor_response(mode, user_query=None, land_context=None):
    if mode == "general":
        prompt = f"""
        You are a highly experienced Indian Real Estate Strategic Advisor.
        
        User Query: {user_query}
        
        Provide a strategic, data-driven, and professional response. Focus on market trends, legal considerations, and investment strategy. Use markdown formatting.
        """
    else:
        # Personalized mode
        prompt = f"""
        You are a Strategic Real Estate Advisor. Provide 'Final Insights' for this specific land asset.
        
        Asset Context:
        - Location: {land_context.get('district')}
        - Year: {land_context.get('year')}
        - AI Optimized Price: ₹{land_context.get('final_price'):,.0f} per acre
        - ML Base Price: ₹{land_context.get('base_price'):,.0f}
        - Soil Quality: {json.dumps(land_context.get('soil_data'))}
        - User Input Factors: {json.dumps(land_context.get('user_inputs'))}
        
        Task: Provide a concise, high-impact 'Executive Insight' (3-4 bullet points). What should the investor do specifically with this land? What is the single biggest opportunity and single biggest risk?
        """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"🚨 AI Advisor failed to process request: {str(e)}"

def get_chat_response(chat_history):
    """
    Handles continuous multi-turn chat.
    chat_history: list of dicts with {"role": "user/assistant", "content": "text"}
    """
    try:
        # Convert history to Gemini format
        gemini_history = []
        for msg in chat_history[:-1]: # All but the last one
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=gemini_history)
        last_message = chat_history[-1]["content"]
        response = chat.send_message(last_message)
        return response.text
    except Exception as e:
        return f"🚨 Chat error: {str(e)}"
