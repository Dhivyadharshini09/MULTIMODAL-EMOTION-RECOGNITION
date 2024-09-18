import os
import logging
import pandas as pd
import re
import requests  # For API requests
from moviepy.editor import VideoFileClip
from indicnlp.tokenize import indic_tokenize
from pydub import AudioSegment
from pydub.silence import split_on_silence
from Levenshtein import distance  # For spell correction (Levenshtein distance)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable to cache Tamil lexicon
tamil_lexicon = []

# Function to fetch Tamil dictionary from an API
def fetch_tamil_lexicon():
    global tamil_lexicon
    try:
        # Replace with actual Tamil dictionary API endpoint
        api_url = "https://tamil-dictionary-api.example.com/v1/words"
        response = requests.get(api_url)

        if response.status_code == 200:
            # Assuming the API returns a JSON response with a list of words
            tamil_lexicon = response.json()  # This should be a list of Tamil words
            logging.info("Fetched Tamil lexicon from API")
        else:
            logging.error(f"Failed to fetch lexicon: {response.status_code}")
    except Exception as e:
        logging.error(f"Error fetching Tamil lexicon: {e}")

# Function to correct Tamil spelling using a Levenshtein distance-based approach
def correct_spelling(word):
    if not tamil_lexicon:
        fetch_tamil_lexicon()  # Ensure lexicon is loaded
    suggestions = [(w, distance(word, w)) for w in tamil_lexicon]
    suggestions = sorted(suggestions, key=lambda x: x[1])
    return suggestions[0][0] if suggestions else word  # Return the closest match or the original word

# Function to clean, correct spelling, and preprocess Tamil text
def preprocess_tamil_text(text):
    # Step 1: Lowercasing
    text = text.lower()
    
    # Step 2: Remove unwanted characters (keep Tamil script characters and spaces)
    text = re.sub(r'[^ஂ-௺\s]', '', text)
    
    # Step 3: Tokenization using IndicNLP
    tokens = indic_tokenize.trivial_tokenize(text, 'ta')
    
    # Step 4: Spell correction (without removing stopwords)
    corrected_tokens = [correct_spelling(token) for token in tokens]
    
    # Step 5: Join the cleaned tokens back into a string
    preprocessed_text = ' '.join(corrected_tokens)
    
    return preprocessed_text

# Function to sanitize file names by removing non-ASCII characters
def sanitize_filename(filename):
    # Remove non-ASCII characters and replace them with an underscore
    sanitized_filename = re.sub(r'[^\x00-\x7F]', '_', filename)
    return sanitized_filename

# Function to preprocess audio
def preprocess_audio(audio_path, preprocessed_audio_path):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(audio_path)

        # Normalize the audio (set to -20 dBFS)
        normalized_audio = audio.normalize()

        # Trim silence (assumes silence is < -40 dBFS)
        segments = split_on_silence(normalized_audio, silence_thresh=-40)
        if segments:
            trimmed_audio = sum(segments)
        else:
            trimmed_audio = normalized_audio

        # Export the preprocessed audio
        trimmed_audio.export(preprocessed_audio_path, format="wav")
        logging.info(f"Preprocessed audio saved to {preprocessed_audio_path}")

    except Exception as e:
        logging.error(f"Error preprocessing audio {audio_path}: {e}")

# Function to preprocess text
def preprocess_text(text, preprocessed_text_path):
    preprocessed_text = preprocess_tamil_text(text)
    with open(preprocessed_text_path, "w", encoding="utf-8") as f:
        f.write(preprocessed_text)
    logging.info(f"Preprocessed text saved to {preprocessed_text_path}")

# Function to process and move unprocessed files
def process_files(audio_folder, text_folder, output_audio_folder, output_text_folder, csv_path):
    # Ensure the output folders exist
    os.makedirs(output_audio_folder, exist_ok=True)
    os.makedirs(output_text_folder, exist_ok=True)

    try:
        audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.wav')]
        text_files = [f for f in os.listdir(text_folder) if f.endswith('.txt')]

        for audio_file in audio_files:
            # Path to unprocessed audio and text files
            audio_path = os.path.join(audio_folder, audio_file)
            text_path = os.path.join(text_folder, audio_file.replace('.wav', '.txt'))

            if not os.path.exists(text_path):
                logging.warning(f"Text file for audio {audio_file} does not exist.")
                continue

            # Paths for preprocessed audio and text
            preprocessed_audio_path = os.path.join(output_audio_folder, f"{os.path.splitext(audio_file)[0]}_preprocessed.wav")
            preprocessed_text_path = os.path.join(output_text_folder, f"{os.path.splitext(audio_file)[0]}_preprocessed.txt")

            # Preprocess audio and text
            preprocess_audio(audio_path, preprocessed_audio_path)
            
            with open(text_path, "r", encoding="utf-8") as f:
                text = f.read()

            preprocess_text(text, preprocessed_text_path)

            # Store data in CSV
            data = {
                "audio_path": [preprocessed_audio_path],
                "text_path": [preprocessed_text_path],
                "preprocessed_text": [text]  # Add the preprocessed text directly to the CSV
            }
            
            df = pd.DataFrame(data)
            if os.path.exists(csv_path):
                df.to_csv(csv_path, mode='a', header=False, index=False)
            else:
                df.to_csv(csv_path, index=False)

        logging.info(f"Data successfully processed and saved to {csv_path}")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Main function to process all files
def main():
    audio_folder = '/media/dhivyadharshini/DATA/project/audio'
    text_folder = '/media/dhivyadharshini/DATA/project/text_extracted'
    output_audio_folder = '/media/dhivyadharshini/DATA/project/preprocessaudio'
    output_text_folder = '/media/dhivyadharshini/DATA/project/preprocesstext'
    csv_path = '/media/dhivyadharshini/DATA/project/dataset.csv'

    process_files(audio_folder, text_folder, output_audio_folder, output_text_folder, csv_path)

# Run the main function
if __name__ == "__main__":
    main()
