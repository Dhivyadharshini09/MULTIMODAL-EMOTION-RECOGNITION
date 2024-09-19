import os
import logging
import pandas as pd
import re
from indicnlp.tokenize import indic_tokenize
from pydub import AudioSegment
from pydub.silence import split_on_silence
from Levenshtein import distance
import pdfplumber
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pdf_file = "/home/dhivyadharshini/Downloads/nn/Lexicon_text.pdf"
tamil_lexicon = {}
with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        lines = text.split('\n')
        for line in lines:
            if ":" in line:
                word, meaning = line.split(":", 1)
                tamil_lexicon[word.strip()] = meaning.strip()

json_file = "lexicon.json"

def correct_spelling(word):
    suggestions = [(w, distance(word, w)) for w in tamil_lexicon]
    suggestions = sorted(suggestions, key=lambda x: x[1])
    return suggestions[0][0] if suggestions else word

def preprocess_tamil_text(text):
    text = text.lower()
    text = re.sub(r'[^ஂ-௺\s]', '', text)
    tokens = indic_tokenize.trivial_tokenize(text, 'ta')    
    corrected_tokens = [correct_spelling(token) for token in tokens]
    preprocessed_text = ' '.join(corrected_tokens)
    return preprocessed_text

def sanitize_filename(filename):
    sanitized_filename = re.sub(r'[^\x00-\x7F]', '_', filename)
    return sanitized_filename

def preprocess_audio(audio_path, preprocessed_audio_path):
    try:
        audio = AudioSegment.from_file(audio_path)
        normalized_audio = audio.normalize()
        segments = split_on_silence(normalized_audio, silence_thresh=-40)
        trimmed_audio = sum(segments) if segments else normalized_audio
        trimmed_audio.export(preprocessed_audio_path, format="wav")
        logging.info(f"Preprocessed audio saved to {preprocessed_audio_path}")
    except Exception as e:
        logging.error(f"Error preprocessing audio {audio_path}: {e}")

def preprocess_text(text, preprocessed_text_path):
    preprocessed_text = preprocess_tamil_text(text)
    if preprocessed_text:  
        with open(preprocessed_text_path, "w", encoding="utf-8") as f:
            f.write(preprocessed_text)
        logging.info(f"Preprocessed text saved to {preprocessed_text_path}")
    else:
        logging.warning(f"Preprocessed text is empty for input text: {text}")

def process_files(audio_folder, text_folder, output_audio_folder, output_text_folder, csv_path):
    os.makedirs(output_audio_folder, exist_ok=True)
    os.makedirs(output_text_folder, exist_ok=True)

    try:
        audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.wav')]
        text_files = [f for f in os.listdir(text_folder) if f.endswith('.txt')]

        for audio_file in audio_files:
            base_name = os.path.splitext(audio_file)[0]
            audio_path = os.path.join(audio_folder, audio_file)
            text_path = os.path.join(text_folder, f"{base_name}.txt")

            if not os.path.exists(text_path):
                logging.warning(f"Text file for audio {audio_file} does not exist.")
                continue

            preprocessed_audio_path = os.path.join(output_audio_folder, f"p_{base_name}.wav")
            preprocessed_text_path = os.path.join(output_text_folder, f"p_{base_name}.txt")
            preprocess_audio(audio_path, preprocessed_audio_path)
            
            with open(text_path, "r", encoding="utf-8") as f:
                text = f.read()

            preprocess_text(text, preprocessed_text_path)

            data = {
                "audio_path": [preprocessed_audio_path],
                "text_path": [preprocessed_text_path],
                "preprocessed_text": [text]
            }
            
            df = pd.DataFrame(data)
            if os.path.exists(csv_path):
                df.to_csv(csv_path, mode='a', header=False, index=False)
            else:
                df.to_csv(csv_path, index=False)

        logging.info(f"Data successfully processed and saved to {csv_path}")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main():
    audio_folder = '/media/dhivyadharshini/DATA/project/audio'
    text_folder = '/media/dhivyadharshini/DATA/project/text_extracted'
    output_audio_folder = '/media/dhivyadharshini/DATA/project/preprocessaudi'
    output_text_folder = '/media/dhivyadharshini/DATA/project/prevideo'
    csv_path = '/media/dhivyadharshini/DATA/project/datset.csv'

    process_files(audio_folder, text_folder, output_audio_folder, output_text_folder, csv_path)

if __name__ == "__main__":
    main()
