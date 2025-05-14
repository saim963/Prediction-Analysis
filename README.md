# Next-Word Prediction Explorer

An interactive web application that uses AI to predict the next word in a sentence and provides detailed analysis of the prediction process.

## Features

- Real-time next-word prediction
- Confidence scores for predictions
- Attention visualization
- Grammar context analysis
- Detailed reasoning for predictions

## Deployment

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your NVIDIA API key:
   ```
   NVIDIA_API_KEY=your_api_key_here
   ```
5. Run the application:
   ```bash
   python app.py
   ```

### Production Deployment

1. Set up environment variables in your hosting platform:

   - `NVIDIA_API_KEY`: Your NVIDIA API key
   - `PORT`: Port number (optional, defaults to 5000)

2. Deploy to Render:
   - Connect your GitHub repository
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `gunicorn app:app`

## Environment Variables

- `NVIDIA_API_KEY`: Required. Your NVIDIA API key for the language model
- `PORT`: Optional. The port to run the application on (default: 5000)

## Error Handling

The application includes comprehensive error handling for:

- API failures
- Invalid responses
- Network issues
- Rate limiting

## Security

- API keys are stored as environment variables
- Input validation and sanitization
- Rate limiting to prevent abuse
- Error messages don't expose sensitive information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
