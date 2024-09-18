import cv2
import os

# Path to input and output folders
input_folder = '/media/dhivyadharshini/DATA/project/output_videos'
output_folder = '/media/dhivyadharshini/DATA/project/preprocessvideo'

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Load a pre-trained model (e.g., for face detection)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def preprocess_video(input_video_path, output_video_path):
    # Create a VideoCapture object
    cap = cv2.VideoCapture(input_video_path)

    # Check if the video was opened successfully
    if not cap.isOpened():
        print(f"Error opening video file: {input_video_path}")
        return

    # Get original video properties
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Define new size for resizing (640px width, maintaining aspect ratio)
    new_width = 640
    new_height = int((new_width / original_width) * original_height)

    # Initialize VideoWriter to save the processed video
    # Initialize VideoWriter to save the processed video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' codec for MP4 format
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (new_width, new_height))

    #fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #out = cv2.VideoWriter(output_video_path, fourcc, fps, (new_width, new_height))

    prev_frame = None
    frame_count = 0
    frame_interval = fps  # Extract one frame per second

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame
        frame_resized = cv2.resize(frame, (new_width, new_height))

        # Apply Gaussian Blur for denoising
        frame_denoised = cv2.GaussianBlur(frame_resized, (5, 5), 0)

        # Motion detection
        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, frame_denoised)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            # Optionally, further processing for motion detection

        prev_frame = frame_denoised

        # Face detection
        gray_frame = cv2.cvtColor(frame_denoised, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame_denoised, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Write the processed frame to the output video
        out.write(frame_denoised)

        frame_count += 1
        if frame_count % frame_interval == 0:
            # Save a frame every second (or as specified by frame_interval)
            cv2.imwrite(f"{output_folder}/frame_{frame_count}.jpg", frame_denoised)

    # Release video objects and close windows
    cap.release()
    out.release()

# Iterate over all video files in the input folder
for video_file in os.listdir(input_folder):
    if video_file.endswith('.mp4'):  # Check if the file is a video
        input_video_path = os.path.join(input_folder, video_file)
        output_video_path = os.path.join(output_folder, video_file)  # Save with the same name in the output folder
        preprocess_video(input_video_path, output_video_path)

print("Processing complete.")