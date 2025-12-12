from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import json
import re

# Load .env file only if it exists (local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, using system env variables (Vercel)



app = Flask(__name__)

# ------------------------------
#  CONFIGURE GROQ CLIENT
# ------------------------------

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("ERROR: GROQ_API_KEY not found in environment variables")

# Create Groq client (OpenAI compatible)
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

print("API Key present:", bool(api_key))


# ------------------------------
#  CLEAN JSON FROM MODEL OUTPUT
# ------------------------------

def clean_json_response(response_text):
    """Extracts the first valid JSON object from the response."""
    response_text = response_text.strip()
    
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]
    
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    response_text = response_text.strip()
    
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    
    if json_start == -1 or json_end <= 0:
        return None

    return response_text[json_start:json_end]


# ------------------------------
#  ROUTES
# ------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        input_phrase = data.get('phrase', '')

        if not input_phrase:
            return jsonify({'error': 'No phrase provided'}), 400

        if not api_key:
            return jsonify({'error': 'GROQ_API_KEY not found'}), 500

        prompt = f'''Given the phrase "{input_phrase}", predict the next likely words.

Return ONLY this exact JSON structure with no additional text:

{{
    "predictions": [
        {{
            "word": "predicted_word_1",
            "confidence": 0.85,
            "attention": [0.1, 0.2, 0.3, 0.2, 0.2],
            "reasoning": "Why this word fits"
        }},
        {{
            "word": "predicted_word_2",
            "confidence": 0.72,
            "attention": [0.15, 0.25, 0.25, 0.2, 0.15],
            "reasoning": "Why this word fits"
        }},
        {{
            "word": "predicted_word_3",
            "confidence": 0.65,
            "attention": [0.2, 0.2, 0.2, 0.2, 0.2],
            "reasoning": "Why this word fits"
        }}
    ],
    "grammar_context": "Brief grammar analysis of the input phrase",
    "reasoning": {{
        "syntactic_analysis": "Sentence structure analysis",
        "semantic_context": "Meaning and context analysis",
        "common_patterns": "Common language patterns identified"
    }}
}}'''

        print("Making API call...")
        print(f"Input phrase: {input_phrase}")

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a JSON-only response bot. Return ONLY valid JSON with no markdown, no explanations, no extra text. Start your response with { and end with }."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )

        raw_output = completion.choices[0].message.content
        print("Raw model response:", raw_output)

        cleaned = clean_json_response(raw_output)
        
        if not cleaned:
            fallback_response = {
                "predictions": [
                    {
                        "word": "the",
                        "confidence": 0.7,
                        "attention": [0.2, 0.2, 0.2, 0.2, 0.2],
                        "reasoning": "Common continuation word"
                    }
                ],
                "grammar_context": "Analysis unavailable",
                "reasoning": {
                    "syntactic_analysis": "Could not parse model response",
                    "semantic_context": "Please try again",
                    "common_patterns": "N/A"
                }
            }
            return jsonify({'response': fallback_response})

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return jsonify({'error': f'Invalid JSON returned by model: {str(e)}'}), 500

        if 'predictions' not in parsed:
            parsed['predictions'] = []
        if 'grammar_context' not in parsed:
            parsed['grammar_context'] = "N/A"
        if 'reasoning' not in parsed:
            parsed['reasoning'] = {
                "syntactic_analysis": "N/A",
                "semantic_context": "N/A", 
                "common_patterns": "N/A"
            }

        return jsonify({'response': parsed})

    except Exception as e:
        print("Internal error:", str(e))
        return jsonify({'error': str(e)}), 500


# ✅ IMPORTANT: Remove or modify the if __name__ block for Vercel
if __name__ == '__main__':
    app.run(debug=True)

# ✅ Vercel needs this - expose the app
app = app