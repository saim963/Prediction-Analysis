from flask import Flask, render_template, request, jsonify
import openai
import os
from dotenv import load_dotenv
import json
import re
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Set up file handler
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

app = Flask(__name__)

# Initialize OpenAI client with NVIDIA API
openai.api_base = "https://integrate.api.nvidia.com/v1"
api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    logger.warning("NVIDIA_API_KEY not found in environment variables")
else:
    # Validate API key format
    if not re.match(r'^[A-Za-z0-9-_]{20,}$', api_key):
        logger.warning("NVIDIA_API_KEY format appears invalid")
    openai.api_key = api_key

def clean_json_response(response):
    """Clean and validate JSON response from API."""
    if not response:
        logger.error("Empty response received")
        return None
        
    # Find the first occurrence of a JSON object
    json_start = response.find('{')
    json_end = response.rfind('}') + 1
    
    if json_start == -1 or json_end == 0:
        logger.error(f"No JSON found in response: {response}")
        return None
        
    json_str = response[json_start:json_end]
    
    # Try to parse it to validate it's proper JSON
    try:
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in response: {json_str}")
        logger.error(f"JSON error: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        input_phrase = data.get('phrase', '')
        
        if not input_phrase:
            logger.error("No phrase provided in request")
            return jsonify({'error': 'No phrase provided'}), 400

        if not api_key:
            logger.error("NVIDIA_API_KEY not found in environment variables")
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

        logger.info(f"Making API call for phrase: {input_phrase}")

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
            logger.debug(f"Raw API response: {full_response}")

            # Clean the response to extract only the JSON part
            cleaned_response = clean_json_response(full_response)
            if not cleaned_response:
                logger.error("No valid JSON found in the response")
                return jsonify({'error': 'No valid JSON found in the response'}), 500

            # Try to parse the response as JSON
            try:
                result = json.loads(cleaned_response)
                # Validate the response format
                if not isinstance(result, dict):
                    logger.error("Invalid response format: not a JSON object")
                    return jsonify({'error': 'Invalid response format: response must be a JSON object'}), 500
                if 'predictions' not in result:
                    logger.error("Invalid response format: missing predictions field")
                    return jsonify({'error': 'Invalid response format: missing predictions field'}), 500
                if not isinstance(result['predictions'], list):
                    logger.error("Invalid response format: predictions is not a list")
                    return jsonify({'error': 'Invalid response format: predictions must be a list'}), 500
                
                return jsonify({'response': cleaned_response})
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Failed to parse response: {cleaned_response}")
                return jsonify({'error': f'Invalid JSON response from API: {str(e)}'}), 500

        except Exception as api_error:
            logger.error(f"API call failed: {str(api_error)}")
            return jsonify({'error': f'API call failed: {str(api_error)}'}), 500

    except Exception as e:
        logger.error(f"Error in predict route: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Use environment variable for port, default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 