import os
import logging
import cv2
import speech_recognition as sr
import pandas as pd
from moviepy.editor import VideoFileClip

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to find the highest numbered clip in the output folder
def get_highest_clip_number(output_folder, base_name):
    clips = [f for f in os.listdir(output_folder) if f.startswith(base_name) and f.endswith('.mp4')]
    if not clips:
        return 0  # No clips found, start from 1
    # Extract the numbers from filenames like "video12.mp4"
    clip_numbers = [int(f[len(base_name):-4]) for f in clips if f[len(base_name):-4].isdigit()]
    return max(clip_numbers) if clip_numbers else 0

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

# Function to extract text and timestamps from audio
def extract_utterances_from_audio(audio_path):
    recognizer = sr.Recognizer()
    utterances = []
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
        # Extracting text
        transcript = recognizer.recognize_google(audio_data, language='ta-IN', show_all=True)
        
        if 'alternative' in transcript:
            for segment in transcript['alternative']:
                if 'transcript' in segment:
                    utterances.append(segment['transcript'])
        
        logging.info(f"Extracted utterances from {audio_path}")
    except sr.UnknownValueError:
        logging.warning(f"Could not understand audio in {audio_path}")
    except sr.RequestError as e:
        logging.error(f"Error with the speech recognition request for {audio_path}: {e}")
    
    return utterances

# Function to split the video into fixed-duration segments and name them continuously
def split_video_fixed_duration(video_path, duration, output_folder, base_name, start_clip_number):
    try:
        video = VideoFileClip(video_path)
        video_duration = video.duration
        current_time = 0
        clip_number = start_clip_number

        while current_time < video_duration:
            end_time = min(current_time + duration, video_duration)
            output_path = os.path.join(output_folder, f"{base_name}{clip_number}.mp4")
            video.subclip(current_time, end_time).write_videofile(output_path)
            logging.info(f"Saved split video to {output_path}")
            current_time += duration
            clip_number += 1

        video.close()
        return clip_number  # Return the last clip number used
    except Exception as e:
        logging.error(f"Error splitting video {video_path}: {e}")
        return start_clip_number

# Process video and split into fixed-duration clips
def process_video(video_path, audio_path, text_folder, output_folder, csv_path, base_name, start_clip_number):
    video_duration, audio_duration = extract_audio_from_video(video_path, audio_path)
    utterances = extract_utterances_from_audio(audio_path)
    
    # Save extracted text in a file inside text_extracted folder
    text_file = os.path.join(text_folder, f"{os.path.splitext(os.path.basename(video_path))[0]}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        for utt in utterances:
            f.write(utt + '\n')
    logging.info(f"Text saved to {text_file}")
    
    # Split the video into 30-second clips
    last_clip_number = split_video_fixed_duration(video_path, 30, output_folder, base_name, start_clip_number)
    
    # Store data in a CSV file, including the extracted text, video, and audio durations
    data = {
        "video_path": [video_path],
        "audio_path": [audio_path],
        "text_path": [text_file],
        "extracted_text": [" ".join(utterances)],
        "video_duration": [video_duration],
        "audio_duration": [audio_duration]
    }
    
    df = pd.DataFrame(data)
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_path, index=False)
    
    return last_clip_number

# Main function to process all videos in the folder
def main():
    video_folder = '/home/dhivyadharshini/Downloads/nn'
    audio_folder = 'audio'
    text_folder = 'text_extracted'
    output_folder = '/media/dhivyadharshini/DATA/project/output_videos'
    csv_path = 'dataset.csv'
    base_name = "video"

    # Ensure the output folders exist
    os.makedirs(audio_folder, exist_ok=True)
    os.makedirs(text_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    # Get the highest existing clip number in the output folder
    start_clip_number = get_highest_clip_number(output_folder, base_name) + 1

    try:
        for video_file in os.listdir(video_folder):
            if video_file.endswith('.mp4'):
                video_path = os.path.join(video_folder, video_file)
                audio_path = os.path.join(audio_folder, f"{os.path.splitext(video_file)[0]}.wav")
                start_clip_number = process_video(video_path, audio_path, text_folder, output_folder, csv_path, base_name, start_clip_number)

        logging.info(f"Data successfully processed and saved to {csv_path}")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Run the main function
if __name__ == "__main__":
    main()
