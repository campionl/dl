import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Webcam non trovata!")
else:
    print("✅ Webcam trovata.")
cap.release()
