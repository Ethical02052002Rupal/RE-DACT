import cv2
import pyautogui
import numpy as np
import os

class redact_video:
    def __init__(self, vid_path):
        cap = cv2.VideoCapture(vid_path)

        # Correct paths to model files
        model_dir = os.path.join(os.path.dirname(__file__), "face_detector")
        proto_path = os.path.join(model_dir, "deploy.prototxt")
        model_path = os.path.join(model_dir, "res10_300x300_ssd_iter_140000.caffemodel")

        # Load the DNN face detector model
        if not os.path.exists(proto_path) or not os.path.exists(model_path):
            raise FileNotFoundError("Model files not found. Please download them.")

        face_net = cv2.dnn.readNetFromCaffe(proto_path, model_path)

        # Get screen resolution
        screen_width, screen_height = pyautogui.size()
        
        # Create a resizable window
        cv2.namedWindow('Redacted Video', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Redacted Video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_height, frame_width = frame.shape[:2]
            aspect_ratio = frame_width / frame_height
            new_width = screen_width
            new_height = int(screen_width / aspect_ratio)
            if new_height > screen_height:
                new_height = screen_height
                new_width = int(screen_height * aspect_ratio)

            frame = cv2.resize(frame, (new_width, new_height))
            
            # Prepare input for DNN model
            blob = cv2.dnn.blobFromImage(frame, scalefactor=1.0, size=(300, 300), mean=(104.0, 177.0, 123.0))
            face_net.setInput(blob)
            detections = face_net.forward()

            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.5:  # Confidence threshold
                    box = detections[0, 0, i, 3:7] * np.array([new_width, new_height, new_width, new_height])
                    (x, y, x_max, y_max) = box.astype("int")
                    expansion=40
                    x=max(x-expansion, 0)
                    y=max(y-expansion, 0)
                    x_max=min(x_max+expansion, new_width)
                    y_max=min(y_max+expansion, new_height)
                    frame[y:y_max, x:x_max] = np.zeros((y_max - y, x_max - x, 3), dtype=np.uint8)
                    # frame[y:y_max, x:x_max] = np.zeros((y_max - y, x_max - x, 3), dtype=np.uint8)  # Blackout the detected face
            
            cv2.imshow('Redacted Video', frame)
            
            if cv2.waitKey(25) & 0xFF == 13:  # Press Enter key to exit
                break
        
        cap.release()
        cv2.destroyAllWindows()
