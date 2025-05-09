from flask import Flask, render_template, request, jsonify
import openai
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client with NVIDIA API
openai.api_base = "https://integrate.api.nvidia.com/v1"
api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    print("Warning: NVIDIA_API_KEY not found in environment variables")
else:
    # Validate API key format
    if not re.match(r'^[A-Za-z0-9-_]{20,}$', api_key):
        print("Warning: NVIDIA_API_KEY format appears invalid")
    openai.api_key = api_key

def clean_json_response(response):
    # Find the first occurrence of a JSON object
    json_start = response.find('{')
    json_end = response.rfind('}') + 1
    
    if json_start == -1 or json_end == 0:
        return None
        
    json_str = response[json_start:json_end]
    return json_str

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
            return jsonify({'error': 'NVIDIA_API_KEY not found in environment variables'}), 500

        # Create the prompt for prediction with explicit JSON formatting
        prompt = f'''You are a language model that predicts next words. Given the phrase "{input_phrase}", provide ONLY a JSON response with the following structure. Do not include any other text, explanations, or thinking process:

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

IMPORTANT: Respond with ONLY the JSON object. No other text, no thinking process, no explanations.'''

        print(f"Making API call with prompt: {prompt}")  # Debug print

        try:
            # Get completion from NVIDIA API without streaming
            completion = openai.ChatCompletion.create(
                model="deepseek-ai/deepseek-r1",
                messages=[
                    {"role": "system", "content": "You are a JSON-only response generator. Never include thinking process or explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                top_p=0.7,
                max_tokens=4096,
                stream=False
            )
            
            # Get the full response
            full_response = completion.choices[0].message.content
            print(f"Raw API response: {full_response}")  # Debug print

            # Clean the response to extract only the JSON part
            cleaned_response = clean_json_response(full_response)
            if not cleaned_response:
                raise ValueError("No valid JSON found in the response")

            # Try to parse the response as JSON
            try:
                result = json.loads(cleaned_response)
                # Validate the response format
                if not isinstance(result, dict):
                    raise ValueError("Invalid response format: response must be a JSON object")
                if 'predictions' not in result:
                    raise ValueError("Invalid response format: missing 'predictions' field")
                if not isinstance(result['predictions'], list):
                    raise ValueError("Invalid response format: 'predictions' must be a list")
                
                return jsonify({'response': cleaned_response})
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")  # Debug print
                print(f"Failed to parse response: {cleaned_response}")  # Debug print
                return jsonify({'error': f'Invalid JSON response from API: {str(e)}'}), 500
            except ValueError as e:
                print(f"Response validation error: {str(e)}")  # Debug print
                return jsonify({'error': str(e)}), 500

        except Exception as api_error:
            print(f"API call failed: {str(api_error)}")
            return jsonify({'error': f'API call failed: {str(api_error)}'}), 500

    except Exception as e:
        print(f"Error in predict route: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run() 