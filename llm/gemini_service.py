import os
import google.generativeai as genai
from dotenv import load_dotenv
from logger_config import log # Import the centralized logger

def get_sentiment(text: str) -> str:
    """
    Analyzes the sentiment of a given text using the Gemini API.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        log.warning("GEMINI_API_KEY not found in .env file. Returning 'Neutral' sentiment.")
        return "Neutral"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
        Analyze the sentiment of the following financial news headline.
        Classify it as 'Positive', 'Negative', or 'Neutral'.
        Return only the single word classification.

        Headline: "{text}"
        """
        
        # --- Logging the request ---
        log.info("--- Calling Gemini API ---")
        log.info(f"Model: gemini-flash-latest")
        log.info(f"Request Body (Prompt):\n{prompt}")
        
        response = model.generate_content(prompt)
        
        # --- Logging the response ---
        log.info(f"Response Body (Raw Text): {response.text}")
        
        sentiment = response.text.strip().capitalize()
        
        if sentiment in ['Positive', 'Negative', 'Neutral']:
            log.info(f"Final Sentiment: {sentiment}")
            log.info("--- Gemini API Call End ---")
            return sentiment
        else:
            log.warning(f"Unexpected sentiment format '{sentiment}'. Defaulting to Neutral.")
            log.info("--- Gemini API Call End ---")
            return "Neutral"
            
    except Exception as e:
        log.error(f"Error during Gemini API call: {e}")
        log.info("--- Gemini API Call End ---")
        return "Neutral"

if __name__ == '__main__':
    # Example Usage:
    headline1 = "Apple's iPhone 15 sales exceed all expectations, driving stock to new highs."
    get_sentiment(headline1)
