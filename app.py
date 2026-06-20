import cv2
import mediapipe as mp
import numpy as np
import os
import pytesseract
try:
    import speech_recognition as sr
except ImportError:
    sr = None
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer


os.makedirs("images", exist_ok=True)
os.makedirs("notes", exist_ok=True)
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

ocr_text = ""
ocr_cooldown = 0
notes_history = []

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)

prev_x = 0
prev_y = 0

smooth_x = 0
smooth_y = 0

smooth_factor = 0.25

canvas = None
canvases = []
total_pages = 5
current_page = 0

draw_color = (255, 0, 255)
eraser_mode = False

brush_size = 5

save_message = ""
save_counter = 0
voice_text = ""

while True:
    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    if not canvases:
        canvases = [np.zeros_like(frame) for _ in range(total_pages)]

    canvas = canvases[current_page]

    cv2.rectangle(frame, (0, 0), (100, 80), (0, 0, 255), -1)
    cv2.rectangle(frame, (100, 0), (200, 80), (0, 255, 0), -1)
    cv2.rectangle(frame, (200, 0), (300, 80), (255, 0, 0), -1)
    cv2.rectangle(frame, (300, 0), (400, 80), (255, 0, 255), -1)
    cv2.rectangle(frame, (400, 0), (500, 80), (120, 120, 120), -1)
    cv2.rectangle(frame, (500, 0), (640, 80), (0, 0, 0), -1)

    cv2.putText(
        frame,
        "RED",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        "GREEN",
        (105, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        "BLUE",
        (220, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        "PURPLE",
        (305, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        "ERASER",
        (405, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        "CLEAR",
        (530, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.rectangle(frame, (0, 80), (120, 140), (70, 70, 70), -1)
    cv2.rectangle(frame, (120, 80), (240, 140), (100, 100, 100), -1)
    cv2.rectangle(frame, (240, 80), (360, 140), (130, 130, 130), -1)

    cv2.putText(
        frame,
        "SMALL",
        (15, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        "MEDIUM",
        (125, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        "LARGE",
        (255, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
            )

            h, w, _ = frame.shape
            index_tip = hand_landmarks.landmark[8]

            raw_x = int(index_tip.x * w)
            raw_y = int(index_tip.y * h)

            smooth_x = int(
            smooth_x + (raw_x - smooth_x) * smooth_factor
            )

            smooth_y = int(
            smooth_y + (raw_y - smooth_y) * smooth_factor
            )

            cx = smooth_x
            cy = smooth_y

            index_up = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
            middle_up = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y

            if index_up and not middle_up:
                if eraser_mode:
                    cv2.putText(
                        frame,
                        "ERASER MODE",
                        (20, 180),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 255),
                        2,
                    )
                    cv2.circle(canvas, (cx, cy), 25, (0, 0, 0), -1)
                else:
                    cv2.putText(
                        frame,
                        f"DRAW MODE | Size: {brush_size}",
                        (20, 180),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                    )

                    if prev_x != 0 and prev_y != 0:
                        cv2.line(canvas, (prev_x, prev_y), (cx, cy), draw_color, brush_size)

                    prev_x = cx
                    prev_y = cy

            elif index_up and middle_up:
                cv2.putText(
                    frame,
                    "SELECTION MODE",
                    (20, 180),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Brush: {brush_size}",
                    (20, 220),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                )

                prev_x = 0
                prev_y = 0

                if cy < 80:
                    if 0 < cx < 100:
                        draw_color = (0, 0, 255)
                        eraser_mode = False
                    elif 100 < cx < 200:
                        draw_color = (0, 255, 0)
                        eraser_mode = False
                    elif 200 < cx < 300:
                        draw_color = (255, 0, 0)
                        eraser_mode = False
                    elif 300 < cx < 400:
                        draw_color = (255, 0, 255)
                        eraser_mode = False
                    elif 400 < cx < 500:
                        eraser_mode = True
                    elif 500 < cx < 640:
                        canvases[current_page] = np.zeros_like(frame)
                        canvas = canvases[current_page]

                if 80 < cy < 140:
                    if 0 < cx < 120:
                        brush_size = 3
                    elif 120 < cx < 240:
                        brush_size = 7
                    elif 240 < cx < 360:
                        brush_size = 12

            else:
                prev_x = 0
                prev_y = 0

            cv2.putText(
                frame,
                f"Brush: {brush_size}",
                (450, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.circle(frame, (cx, cy), 15, draw_color, -1)
    else:
        prev_x = 0
        prev_y = 0

    frame = cv2.add(frame, canvas)

    if ocr_text:
        cv2.putText(
            frame,
            f"OCR: {ocr_text.strip()[:25]}",
            (20, 220),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

    cv2.putText(
        frame,
        f"Notes: {len(notes_history)}",
        (20, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2,
    )

    cv2.putText(
        frame,
        f"Page {current_page + 1}/{total_pages}",
        (450, 170),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2,
    )

    if voice_text:
        cv2.putText(
            frame,
            f"Voice: {voice_text[:25]}",
            (20, 300),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

    if save_counter > 0:
        cv2.putText(
            frame,
            save_message,
            (300, 470),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            3,
        )
        save_counter -= 1

    cv2.imshow("AI Smart Whiteboard", frame)

    key = cv2.waitKeyEx(1)

    if ocr_cooldown > 0:
        ocr_cooldown -= 1

    if key == ord("s"):

        gray_canvas = cv2.cvtColor(
            canvas,
            cv2.COLOR_BGR2GRAY
        )

        cv2.imwrite(
            "images/saved_drawing.png",
            gray_canvas
        )

        save_message = "IMAGE SAVED"
        save_counter = 100

    if key == ord("o") and ocr_cooldown == 0:

        gray = cv2.cvtColor(
            canvas,
            cv2.COLOR_BGR2GRAY
        )

        blurred = cv2.GaussianBlur(
            gray,
            (5, 5),
            0
        )

        _, thresh = cv2.threshold(
            blurred,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        cv2.imshow("OCR Processed Image", thresh)

        ocr_text = pytesseract.image_to_string(
            thresh,
            config="--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        )

        print("OCR Result:", ocr_text.strip())
        recognized_text = ocr_text.strip()
        if recognized_text:
            notes_history.append(recognized_text)
            with open("notes/notes.txt", "a", encoding="utf-8") as notes_file:
                notes_file.write(recognized_text + "\n")

        ocr_cooldown = 50

    if key == ord("n"):
        notes_history.clear()
        with open("notes/notes.txt", "w", encoding="utf-8"):
            pass

    if key == ord("p"):
        notes_path = "notes/notes.txt"
        pdf_path = "notes/notes_export.pdf"

        notes_text = ""
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as notes_file:
                notes_text = notes_file.read().strip()

        if notes_text:
            pdf = SimpleDocTemplate(pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()
            pdf_content = [
                Paragraph("AI Smart Whiteboard Notes", styles["Title"]),
                Spacer(1, 12),
                Paragraph(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    styles["Normal"],
                ),
                Spacer(1, 12),
                Preformatted(notes_text, styles["Code"]),
            ]
            pdf.build(pdf_content)
            save_message = "PDF EXPORTED"
            save_counter = 100
        else:
            save_message = "NO NOTES TO EXPORT"
            save_counter = 100

    if key == ord("v"):
        save_message = "Listening..."
        save_counter = 100
        cv2.putText(
            frame,
            save_message,
            (300, 470),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            3,
        )
        cv2.imshow("AI Smart Whiteboard", frame)
        cv2.waitKey(1)

        if sr is None:
            save_message = "Voice Library Missing"
            save_counter = 100
        else:
            try:
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

                voice_text = recognizer.recognize_google(audio).lower().strip()
                save_message = "Command Recognized"
                save_counter = 100

                if voice_text == "clear":
                    canvases[current_page] = np.zeros_like(frame)
                    canvas = canvases[current_page]
                elif voice_text == "save image":
                    gray_canvas = cv2.cvtColor(
                        canvas,
                        cv2.COLOR_BGR2GRAY
                    )
                    cv2.imwrite(
                        "images/saved_drawing.png",
                        gray_canvas
                    )
                    save_message = "IMAGE SAVED"
                    save_counter = 100
                elif voice_text == "export pdf":
                    notes_path = "notes/notes.txt"
                    pdf_path = "notes/notes_export.pdf"

                    notes_text = ""
                    if os.path.exists(notes_path):
                        with open(notes_path, "r", encoding="utf-8") as notes_file:
                            notes_text = notes_file.read().strip()

                    if notes_text:
                        pdf = SimpleDocTemplate(pdf_path, pagesize=letter)
                        styles = getSampleStyleSheet()
                        pdf_content = [
                            Paragraph("AI Smart Whiteboard Notes", styles["Title"]),
                            Spacer(1, 12),
                            Paragraph(
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                styles["Normal"],
                            ),
                            Spacer(1, 12),
                            Preformatted(notes_text, styles["Code"]),
                        ]
                        pdf.build(pdf_content)
                        save_message = "PDF EXPORTED"
                        save_counter = 100
                    else:
                        save_message = "NO NOTES TO EXPORT"
                        save_counter = 100
                elif voice_text == "clear notes":
                    notes_history.clear()
                    with open("notes/notes.txt", "w", encoding="utf-8"):
                        pass
                    save_message = "Command Recognized"
                    save_counter = 100
                else:
                    save_message = "Unknown Command"
                    save_counter = 100
            except sr.WaitTimeoutError:
                save_message = "Speech Not Recognized"
                save_counter = 100
            except sr.UnknownValueError:
                save_message = "Speech Not Recognized"
                save_counter = 100
            except sr.RequestError:
                save_message = "Recognition Service Error"
                save_counter = 100
            except (OSError, AttributeError):
                save_message = "No Microphone Found"
                save_counter = 100

    if key == 2555904 and current_page < total_pages - 1:
        current_page += 1
        prev_x = 0
        prev_y = 0

    if key == 2424832 and current_page > 0:
        current_page -= 1
        prev_x = 0
        prev_y = 0

    if key == ord("q"):
        break

    

cap.release()
cv2.destroyAllWindows()


