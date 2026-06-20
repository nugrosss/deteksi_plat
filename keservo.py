import serial
import time

# Ganti COM3 sesuai port Arduino
arduino = serial.Serial('COM17', 9600)
time.sleep(2)


# Function untuk menggerakkan servo
def gerak_servo_keluar():

    # Kirim data 1 ke Arduino
    arduino.write(b'2\n')

    print("Servo dijalankan keluar")
def gerak_servo_masuk():

    # Kirim data 1 ke Arduino
    arduino.write(b'1\n')

    print("Servo dijalankan masuk")
if __name__ == "__main__":

        # Baca data dari Arduino
    for i in range(10):  # Contoh membaca 5 data
        gerak_servo_keluar()
        time.sleep(1)  # Delay sebelum membaca data berikutny
        gerak_servo_masuk()
        time.sleep(1)  # Delay sebelum membaca data berikutny