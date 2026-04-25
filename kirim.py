import mysql.connector
from datetime import datetime
import time

DB_CONFIG = {
    "host": "192.168.96.128",      # Sama mesin = localhost
    "user": "diva",   #root 
    "password": "123456",
    "database": "db_foto"
}

def kirim_data_masuk(plat: str, path_foto: str):
    conn = None
    cursor = None
    try:
        with open(path_foto, "rb") as f:
            foto_binary = f.read()

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """INSERT INTO parkir_log (plat, foto, foto_mime, jam_masuk, status)
                 VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (plat, foto_binary, "image/jpeg", datetime.now(), "masuk"))
        conn.commit()

        record_id = cursor.lastrowid
        print(f"[OK] Masuk tersimpan: {plat} | ID: {record_id}")
        return record_id

    except mysql.connector.Error as e:
        print(f"[ERROR] {e}")
        return None

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()

def kirim_data_keluar(id_masuk: int, plat: str):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        jam_keluar = datetime.now()

        cursor.execute("SELECT jam_masuk FROM parkir_log WHERE id = %s", (id_masuk,))
        row = cursor.fetchone()

        durasi_str = "-"
        if row:
            selisih = jam_keluar - row[0]
            mnt = int(selisih.total_seconds() // 60)
            durasi_str = f"{mnt // 60}j {mnt % 60}m"

        cursor.execute(
            "UPDATE parkir_log SET jam_keluar=%s, durasi=%s, status='keluar' WHERE id=%s",
            (jam_keluar, durasi_str, id_masuk)
        )
        conn.commit()

        print(f"[OK] Keluar diupdate: {plat} | Durasi: {durasi_str}")

    except mysql.connector.Error as e:
        print(f"[ERROR] {e}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    # Contoh mobil masuk
    id_data = kirim_data_masuk("A 1234 XY", "D:\\kuliah JTD\\Rakitriset\\Diva\\Screenshot 2024-07-08 152759.png")

    # Simulasi delay (misal 5 detik)
    import time
    time.sleep(0.4)

    # Mobil keluar
    kirim_data_keluar(id_data, "A 1234 XY")
