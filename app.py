from flask import Flask, render_template, request, redirect, url_for
import os
import csv

app = Flask(__name__)

# Folder paths
VIDEO_FOLDER = 'static/preprocessvideo'
AUDIO_FOLDER = 'static/preprocessaudio'
TEXT_FOLDER = 'static/preprocesstext'

# Load media file metadata
def get_media_files():
    videos = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith('.mp4')]
    audio_files = [f.replace('.mp4', '.wav') for f in videos]
    text_files = [f for f in os.listdir(TEXT_FOLDER) if f.endswith('.txt')]
    
    text_file_mapping = {f.replace('.txt', '.mp4'): f for f in text_files}
    
    media_files = []
    for video in videos:
        audio = video.replace('.mp4', '.wav')
        text = text_file_mapping.get(video, None)
        text_file_path = os.path.join(TEXT_FOLDER, text) if text else None
        
        if text_file_path and os.path.exists(text_file_path):
            with open(text_file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        else:
            text_content = "Text not available for this media."
        
        annotation_count = 0
        annotators = []
        
        # Check if this video has annotations already
        if os.path.exists('annotations.csv'):
            with open('annotations.csv', 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == video.split('.')[0]:
                        annotation_count += 1
                        if len(row) > 3:
                            annotators.append(row[2])
        
        media_files.append({
            'video': video,
            'audio': audio,
            'text_content': text_content,
            'annotation_count': annotation_count,
            'annotators': annotators
        })
    
    return media_files

@app.route('/')
def index():
    media_files = get_media_files()
    return render_template('index.html', media_files=media_files)

@app.route('/submit', methods=['POST'])
def submit():
    media_name = request.form['media_name']
    annotator_name = request.form['annotator_name']
    selected_emotion = request.form.get('selected_emotion')
    emotion_rating = request.form.get('emotion_rating')
    comments = request.form.get('comments', '')

    if not selected_emotion or not emotion_rating:
        return redirect(url_for('index'))

    # Save the rating to CSV
    with open('annotations.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([media_name, selected_emotion, annotator_name, emotion_rating, comments])
    
    # Update majority emotion CSV
    update_majority_emotion_csv()

    return redirect(url_for('index'))

def update_majority_emotion_csv():
    annotations = {}
    majority_file = 'majority_emotions.csv'

    # Read existing annotations
    if os.path.exists('annotations.csv'):
        with open('annotations.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                video, emotion, _, _, _ = row
                if video not in annotations:
                    annotations[video] = []
                annotations[video].append(emotion)
    
    # Calculate majority emotion for each video
    majority_emotions = []
    for video, emotions in annotations.items():
        emotion_count = {}
        for emotion in emotions:
            if emotion not in emotion_count:
                emotion_count[emotion] = 0
            emotion_count[emotion] += 1
        majority_emotion = max(emotion_count, key=emotion_count.get)
        majority_emotions.append([video, majority_emotion])
    
    # Write the majority emotions to a new CSV file
    with open(majority_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Video', 'Majority Emotion'])
        writer.writerows(majority_emotions)

if __name__ == '__main__':
    app.run(debug=True)
