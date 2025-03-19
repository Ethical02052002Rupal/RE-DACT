import cv2
import numpy as np
from ultralytics import YOLO

class RedactVideo:
    def process_faces(video_path):
        """Detects faces in the first frame of a video and returns a list of face snapshots."""
        cap = cv2.VideoCapture(video_path)
        model = YOLO("../yolov8n-face.pt", verbose=False)

        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to read video.")
            cap.release()
            return []

        frame_height, frame_width = frame.shape[:2]
        frame = cv2.resize(frame, (frame_width, frame_height))
        results = model(frame)

        face_snapshots = []

        print("\nDetected Faces:")
        for i, box in enumerate(results[0].boxes):
            x, y, x_max, y_max = map(int, box.xyxy[0])

            expansion = 20
            x = max(x - expansion, 0)
            y = max(y - expansion, 0)
            x_max = min(x_max + expansion, frame_width)
            y_max = min(y_max + expansion, frame_height)

            face_crop = frame[y:y_max, x:x_max].copy()
            face_snapshots.append(face_crop)

            print(f"Face {i}: Position ({x}, {y}) to ({x_max}, {y_max})")

            cv2.rectangle(frame, (x, y), (x_max, y_max), (0, 255, 0), 2)
            cv2.putText(frame, f"{i}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            #cv2.imshow(f"Face {i}", face_crop)
            #cv2.waitKey(3000)
            #cv2.destroyWindow(f"Face {i}")

        for idx, face in enumerate(face_snapshots):
            cv2.imwrite(f"media/face_{idx}.jpg", face)

        print("Face snapshots saved.")
        cap.release()
        return face_snapshots


    def redact_faces(video_path, selected_faces, output_path):
        """Redacts selected faces from a video."""
        cap = cv2.VideoCapture(video_path)
        model = YOLO("../yolov8n-face.pt", verbose=False)

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, int(fps), (frame_width, frame_height))

        # cv2.namedWindow("Redacted Video", cv2.WINDOW_NORMAL)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (frame_width, frame_height))
            results = model(frame)

            for i, box in enumerate(results[0].boxes):
                if i in selected_faces:
                    x, y, x_max, y_max = map(int, box.xyxy[0])

                    expansion = 20
                    x = max(x - expansion, 0)
                    y = max(y - expansion, 0)
                    x_max = min(x_max + expansion, frame_width)
                    y_max = min(y_max + expansion, frame_height)

                    frame[y:y_max, x:x_max] = np.zeros((y_max - y, x_max - x, 3), dtype=np.uint8)

            # cv2.imshow("Redacted Video", frame)
            out.write(frame)

            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
        print("Completed!")
        cap.release()
        out.release()
        cv2.destroyAllWindows()
