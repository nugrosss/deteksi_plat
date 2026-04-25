import cv2
from matplotlib import image
import pytesseract
from ultralytics import YOLO
from kirim import kirim_data_masuk, kirim_data_keluar

from collections import deque, Counter

buffer_text = deque(maxlen=5)  # simpan 5 frame terakhir
confirm_threshold = 3         # minimal kemunculan untuk dianggap valid

# Path tesseract
pytesseract.pytesseract.tesseract_cmd = r'D:\ocr\tesseract.exe'

# Load model YOLO
model = YOLO(r"D:\kuliah JTD\belajar aroc\cobaopenvino\divabest_openvino_model", task="detect")

def extract_text_from_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    config = '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text = pytesseract.image_to_string(gray, config=config)

    return text.strip()

def main():
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Kamera tidak terbuka!")
        return

    last_text = ""
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        
        # Jalankan deteksi tiap 5 frame agar FPS tetap stabil
        if frame_count % 5 == 0:
            results = model(frame)

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    class_name = model.names[cls]

                    if class_name != "Plat":
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    h = y2 - y1
                    # Potong dari y1 sampai y1 + setengah tinggi
                    cropped = frame[int(y1) : int(y1 + (h/2)), int(x1) : int(x2)]
                    
                    # Tampilkan hasil crop (Hanya muncul jika ada plat)
                    cv2.imshow("Cropped Plate", cropped) 
                    cv2.imwrite("cropped_plate.jpg", cropped)  # Simpan gambar hasil crop untuk referensi
                    
                    # 2. Ekstrak teks
                    text = extract_text_from_image(cropped)
                    
                    # 3. Gambar kotak (Bounding Box) di frame utama
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # 4. Tampilkan teks hasil OCR di frame utama
                    cv2.putText(frame, text, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                    
                    print(f"Deteksi: {text}")
                    # cv2.imwrite("detected_plate.jpg", frame)  # Simpan gambar hasil crop untuk referensi

                    text = extract_text_from_image(cropped)

                    if text != "":
                        buffer_text.append(text)

                        # Hitung kemunculan teks
                        counter = Counter(buffer_text)
                        most_common_text, count = counter.most_common(1)[0]

                        print(f"Buffer: {list(buffer_text)}")

                        # Jika teks stabil muncul beberapa kali
                        if count >= confirm_threshold and most_common_text != last_text:
                            print(f"Kirim Data: {most_common_text}")

                            cv2.imwrite("detected_plate.jpg", frame)
                            kirim_data_masuk(most_common_text, "detected_plate.jpg")
                            print(f"Data {most_common_text} dikirim ke database.")

                            last_text = most_common_text
                            buffer_text.clear()  # reset buffer setelah kirim
                       

        # Tampilkan frame utama (Selalu diupdate setiap loop)
        cv2.imshow("Detection Result", frame)

        # Tekan 'q' untuk keluar
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()