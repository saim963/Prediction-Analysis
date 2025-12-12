from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import json
import re

app = Flask(__name__)

# ------------------------------
#  CONFIGURE NVIDIA OPENAI CLIENT
# ------------------------------

api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    print("ERROR: NVIDIA_API_KEY not found in environment variables")
else:
    # Relaxed valid key check (NVIDIA keys contain "-" and ".")
    if not re.match(r'^[A-Za-z0-9._\-]+$', api_key):
        print("Warning: NVIDIA_API_KEY format looks unusual (but may still be valid)")

# Create proper NVIDIA client
client = OpenAI(
    api_key=api_key,
    base_url="https://integrate.api.nvidia.com/v1"
)

print("API Key present:", bool(api_key))


# ------------------------------
#  CLEAN JSON FROM MODEL OUTPUT
# ------------------------------

def clean_json_response(response_text):
    """Extracts the first valid JSON object from the response."""
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
            return jsonify({'error': 'NVIDIA_API_KEY not found'}), 500

        # ------------------------------
        #  BUILD PROMPT
        # ------------------------------

        prompt = f'''
You are a language model that predicts next words. Given the phrase "{input_phrase}", provide ONLY a JSON response with the following structure. Do not include any other text, explanations, or thinking process:

{{
    "predictions": [
        {{
            "word": "example1",
            "confidence": 0.8,
            "attention": [0.1, 0.2, 0.3, 0.2, 0.2],
            "reasoning": "Explanation for this prediction"
        }}
    ],
    "grammar_context": "Analysis of the grammar",
    "reasoning": {{
        "syntactic_analysis": "Analysis of sentence structure",
        "semantic_context": "Analysis of meaning",
        "common_patterns": "Analysis of patterns"
    }}
}}

IMPORTANT: Respond with ONLY the JSON object. No other text, no thinking process, no explanations.
'''

        print("Making API call...")

        # ------------------------------
        #  CALL NVIDIA MODEL
        # ------------------------------

        completion = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",  # stable NVIDIA-supported model
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON. No explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )

        raw_output = completion.choices[0].message.content
        print("Raw model response:", raw_output)

        # ------------------------------
        #  CLEAN & VALIDATE JSON
        # ------------------------------

        cleaned = clean_json_response(raw_output)
        if not cleaned:
            return jsonify({'error': 'No valid JSON found in model output'}), 500

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return jsonify({'error': f'Invalid JSON returned by model: {str(e)}'}), 500

        return jsonify({'response': parsed})

    except Exception as e:
        print("Internal error:", str(e))
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run()
