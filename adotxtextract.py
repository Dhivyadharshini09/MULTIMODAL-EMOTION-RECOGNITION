import sys
import os
import logging
import cv2
import speech_recognition as sr
import pandas as pd
from moviepy.editor import VideoFileClip

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract audio from video and get video duration
def extract_audio_from_video(video_path, audio_path):
    try:
        video = VideoFileClip(video_path)
        video_duration = video.duration  # Get video duration
        audio = video.audio
        audio.write_audiofile(audio_path)
        audio_duration = audio.duration  # Get audio duration
        video.close()
        logging.info(f"Extracted audio from {video_path} to {audio_path}")
        return video_duration, audio_duration
    except Exception as e:
        logging.error(f"Error extracting audio from {video_path}: {e}")
        return None, None

# Function to extract text from audio and only take the first recognized alternative
def extract_text_from_audio(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)

        # Extracting text using Google speech recognition for Tamil language
        transcript = recognizer.recognize_google(audio_data, language='ta-IN', show_all=True)

        # Check if 'alternative' is in the transcript and take only the first alternative
        if 'alternative' in transcript and len(transcript['alternative']) > 0:
            text = transcript['alternative'][0].get('transcript', '').strip()  # Get the first alternative
        else:
            text = ""

        logging.info(f"Extracted text from {audio_path}")
        return text
    except sr.UnknownValueError:
        logging.warning(f"Could not understand audio in {audio_path}")
        return ""
    except sr.RequestError as e:
        logging.error(f"Error with the speech recognition request for {audio_path}: {e}")
        return ""

# Process video and save results in CSV
def process_video(video_path, audio_path, text_folder, csv_path):
    video_duration, audio_duration = extract_audio_from_video(video_path, audio_path)
    text = extract_text_from_audio(audio_path)
    
    # Save extracted text in a file inside text_extracted folder
    text_file = os.path.join(text_folder, f"{os.path.splitext(os.path.basename(video_path))[0]}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text)
    logging.info(f"Text saved to {text_file}")
    
    # Store data in a CSV file, including the extracted text, video, and audio durations
    data = {
        "video_path": [video_path],
        "audio_path": [audio_path],
        "text_path": [text_file],
        "extracted_text": [text],
        "video_duration": [video_duration],
        "audio_duration": [audio_duration]
    }
    
    df = pd.DataFrame(data)
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_path, index=False)

# Main function to process all videos in the folder
def main():
    video_folder = '/media/dhivyadharshini/DATA/project/output_videos'
    audio_folder = '/media/dhivyadharshini/DATA/project/audio'
    text_folder = '/media/dhivyadharshini/DATA/project/text_extracted'
    csv_path = '/media/dhivyadharshini/DATA/project/dataset.csv'

    # Ensure the output folders exist
    os.makedirs(audio_folder, exist_ok=True)
    os.makedirs(text_folder, exist_ok=True)

    try:
        for video_file in os.listdir(video_folder):
            if video_file.endswith('.mp4'):
                video_path = os.path.join(video_folder, video_file)
                audio_path = os.path.join(audio_folder, f"{os.path.splitext(video_file)[0]}.wav")
                process_video(video_path, audio_path, text_folder, csv_path)

        logging.info(f"Data successfully processed and saved to {csv_path}")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Run the main function
if __name__ == "__main__":
    main()
