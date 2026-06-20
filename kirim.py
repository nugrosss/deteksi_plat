import mysql.connector
from datetime import datetime
import time

DB_CONFIG = {
    "host": "localhost",      # Sama mesin = localhost
    "user": "root",   #root 
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

def kirim_data_keluar(plat: str):
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Cari data masuk yang cocok
        cursor.execute("""
            SELECT id, jam_masuk
            FROM parkir_log
            WHERE plat = %s AND status = 'masuk'
            ORDER BY jam_masuk DESC
            LIMIT 1
        """, (plat,))

        row = cursor.fetchone()

        if row:
            print(f"[MATCH] Plat ditemukan: {plat}")

            id_masuk = row[0]
            jam_masuk = row[1]
            jam_keluar = datetime.now()

            selisih = jam_keluar - jam_masuk
            mnt = int(selisih.total_seconds() // 60)
            durasi_str = f"{mnt // 60}j {mnt % 60}m"

            cursor.execute("""
                UPDATE parkir_log
                SET jam_keluar=%s,
                    durasi=%s,
                    status='keluar'
                WHERE id=%s
            """, (jam_keluar, durasi_str, id_masuk))

            conn.commit()

            print(f"[OK] Keluar: {plat}")
            return True

        else:
            print(f"[NO MATCH] Plat tidak ditemukan: {plat}")
            return False

    except mysql.connector.Error as e:
        print(f"[ERROR] {e}")
        return False

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    # Contoh mobil masuk
    id_data = kirim_data_masuk("A DIVAAA XY", "D:\\kuliah JTD\\Rakitriset\\Diva\\detected_plate.jpg")

    # # Simulasi delay (misal 5 detik)
    # import time
    # time.sleep(4)

    # Mobil keluar
    # kirim_data_keluar( "A DIVAAA XY")
# http://localhost/dashboard.html