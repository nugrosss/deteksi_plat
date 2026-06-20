"""
security.py — Modul Enkripsi AES-128 CBC
Secure Smart Parking System

Cara pakai:
    from security import encrypt_aes, decrypt_aes, encrypt_image, decrypt_image

Dependensi:
    pip install pycryptodome python-dotenv

Variabel .env yang diperlukan:
    AES_KEY=<32 hex karakter, contoh: 0123456789abcdef0123456789abcdef>
    AES_IV=<32 hex karakter, contoh: abcdef0123456789abcdef0123456789>
"""

import os
import base64
import hashlib
import secrets
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ──────────────────────────────────────────────
#  Muat key & IV dari environment / .env
# ──────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Jika python-dotenv belum di-install, skip


# Cache key & IV agar hanya di-generate SEKALI per sesi
_cached_key: bytes | None = None
_cached_iv:  bytes | None = None

def _load_key_iv() -> tuple[bytes, bytes]:
    """
    Ambil AES_KEY dan AES_IV dari environment variable.
    Keduanya disimpan sebagai hex string (32 karakter = 16 byte).

    Jika belum ada, generate otomatis SEKALI dan cache di memori
    agar encrypt & decrypt dalam sesi yang sama selalu pakai key yang sama.
    """
    global _cached_key, _cached_iv

    # Kembalikan cache jika sudah ada
    if _cached_key and _cached_iv:
        return _cached_key, _cached_iv

    key_hex = os.environ.get("AES_KEY")
    iv_hex  = os.environ.get("AES_IV")

    if not key_hex or not iv_hex:
        # Auto-generate SEKALI — HANYA untuk development!
        # Setelah ini, salin key yang muncul ke file .env
        generated_key = secrets.token_hex(16)  # 16 byte = 128 bit
        generated_iv  = secrets.token_hex(16)
        print("=" * 60)
        print("[PERINGATAN] AES_KEY / AES_IV tidak ditemukan di .env!")
        print("Salin baris berikut ke file .env Anda:\n")
        print(f"AES_KEY={generated_key}")
        print(f"AES_IV={generated_iv}")
        print("=" * 60)
        key_hex = generated_key
        iv_hex  = generated_iv

    try:
        key = bytes.fromhex(key_hex)
        iv  = bytes.fromhex(iv_hex)
    except ValueError:
        raise ValueError("AES_KEY / AES_IV harus berupa hex string yang valid (32 karakter).")

    if len(key) != 16 or len(iv) != 16:
        raise ValueError(
            f"AES_KEY harus 16 byte (128-bit). "
            f"Panjang sekarang: key={len(key)}, iv={len(iv)}"
        )

    # Simpan ke cache agar tidak di-generate ulang
    _cached_key = key
    _cached_iv  = iv

    return key, iv


# ──────────────────────────────────────────────
#  Core: Enkripsi & Dekripsi Teks
# ──────────────────────────────────────────────

def encrypt_aes(plaintext: str) -> str:
    """
    Enkripsi string dengan AES-128 CBC.

    Parameter:
        plaintext (str): Teks asli, misal nomor plat "B 1234 XYZ"

    Return:
        str: Ciphertext dalam format Base64 (aman untuk disimpan di DB / dikirim via MQTT)

    Contoh:
        >>> encrypted = encrypt_aes("B 1234 XYZ")
        >>> print(encrypted)   # "abc123...==" (Base64)
    """
    if not isinstance(plaintext, str):
        raise TypeError(f"encrypt_aes: plaintext harus str, bukan {type(plaintext).__name__}")

    key, iv = _load_key_iv()
    cipher  = AES.new(key, AES.MODE_CBC, iv)

    # Encode UTF-8, lalu padding ke kelipatan 16 byte (PKCS7)
    padded     = pad(plaintext.encode("utf-8"), AES.block_size)
    ciphertext = cipher.encrypt(padded)

    # Encode ke Base64 agar bisa disimpan sebagai teks biasa
    return base64.b64encode(ciphertext).decode("utf-8")


def decrypt_aes(ciphertext_b64: str) -> str:
    """
    Dekripsi hasil encrypt_aes() kembali ke teks asli.

    Parameter:
        ciphertext_b64 (str): Ciphertext dalam format Base64

    Return:
        str: Teks asli (plaintext)

    Contoh:
        >>> original = decrypt_aes(encrypted)
        >>> print(original)   # "B 1234 XYZ"
    """
    if not isinstance(ciphertext_b64, str):
        raise TypeError(f"decrypt_aes: input harus str, bukan {type(ciphertext_b64).__name__}")

    key, iv    = _load_key_iv()
    cipher     = AES.new(key, AES.MODE_CBC, iv)

    try:
        ciphertext = base64.b64decode(ciphertext_b64)
        decrypted  = cipher.decrypt(ciphertext)
        plaintext  = unpad(decrypted, AES.block_size)
        return plaintext.decode("utf-8")
    except (ValueError, KeyError) as e:
        raise ValueError(f"Dekripsi gagal — ciphertext mungkin rusak atau key salah: {e}")


# ──────────────────────────────────────────────
#  Enkripsi & Dekripsi Gambar (Binary)
# ──────────────────────────────────────────────

def encrypt_image(image_bytes: bytes) -> bytes:
    """
    Enkripsi data gambar (bytes) dengan AES-128 CBC.
    Cocok untuk kolom BLOB di MySQL.

    Parameter:
        image_bytes (bytes): Raw bytes dari file gambar

    Return:
        bytes: Encrypted bytes (siap disimpan ke kolom BLOB)

    Contoh:
        >>> with open("foto_plat.jpg", "rb") as f:
        ...     raw = f.read()
        >>> encrypted_blob = encrypt_image(raw)
    """
    if not isinstance(image_bytes, bytes):
        raise TypeError(f"encrypt_image: input harus bytes, bukan {type(image_bytes).__name__}")

    key, iv = _load_key_iv()
    cipher  = AES.new(key, AES.MODE_CBC, iv)
    padded  = pad(image_bytes, AES.block_size)
    return cipher.encrypt(padded)


def decrypt_image(encrypted_bytes: bytes) -> bytes:
    """
    Dekripsi gambar yang dienkrip dengan encrypt_image().

    Parameter:
        encrypted_bytes (bytes): Encrypted bytes dari kolom BLOB

    Return:
        bytes: Raw bytes gambar asli

    Contoh:
        >>> raw_image = decrypt_image(encrypted_blob)
        >>> with open("output.jpg", "wb") as f:
        ...     f.write(raw_image)
    """
    if not isinstance(encrypted_bytes, bytes):
        raise TypeError(f"decrypt_image: input harus bytes, bukan {type(encrypted_bytes).__name__}")

    key, iv = _load_key_iv()
    cipher  = AES.new(key, AES.MODE_CBC, iv)

    try:
        decrypted = cipher.decrypt(encrypted_bytes)
        return unpad(decrypted, AES.block_size)
    except (ValueError, KeyError) as e:
        raise ValueError(f"Dekripsi gambar gagal: {e}")


# ──────────────────────────────────────────────
#  Utilitas Tambahan
# ──────────────────────────────────────────────

def hash_plat(plat: str) -> str:
    """
    Buat hash SHA-256 dari nomor plat.
    Berguna untuk indexing / pencarian di DB tanpa menyimpan plaintext.

    Parameter:
        plat (str): Nomor plat asli, misal "B 1234 XYZ"

    Return:
        str: SHA-256 hex digest (64 karakter)

    Contoh:
        >>> h = hash_plat("B 1234 XYZ")
        # Simpan hash ini ke kolom terpisah untuk keperluan query
    """
    normalized = plat.strip().upper()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def generate_env_template() -> str:
    """
    Generate template .env baru dengan key & IV acak.
    Jalankan sekali saat setup project.

    Return:
        str: Isi .env yang siap disalin
    """
    key = secrets.token_hex(16)
    iv  = secrets.token_hex(16)
    return (
        "# ─── AES-128 CBC Configuration ───────────────────────\n"
        "# JANGAN di-commit ke Git! Tambahkan .env ke .gitignore\n"
        f"AES_KEY={key}\n"
        f"AES_IV={iv}\n"
    )


# ──────────────────────────────────────────────
#  Self-test (jalankan: python security.py)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  SELF-TEST: Modul AES-128 CBC — Smart Parking")
    print("=" * 55)

    # --- 1. Test enkripsi & dekripsi teks (nomor plat)
    sample_plates = ["B 1234 XYZ", "AB 5678 CD", "N 999 ZZ", "W 0001 ABC"]

    print("\n[1] Enkripsi & Dekripsi Nomor Plat")
    print("-" * 55)
    all_passed = True
    for plat in sample_plates:
        enc  = encrypt_aes(plat)
        dec  = decrypt_aes(enc)
        status = "✅ PASS" if dec == plat else "❌ FAIL"
        if dec != plat:
            all_passed = False
        print(f"  Plat     : {plat}")
        print(f"  Encrypted: {enc}")
        print(f"  Decrypted: {dec}")
        print(f"  Status   : {status}")
        print()

    # --- 2. Test hash plat (untuk indexing DB)
    print("[2] Hash SHA-256 Nomor Plat")
    print("-" * 55)
    for plat in sample_plates[:2]:
        h = hash_plat(plat)
        print(f"  {plat:15s} → {h[:32]}...")

    # --- 3. Test enkripsi gambar (dummy bytes)
    print("\n[3] Enkripsi & Dekripsi Data Gambar (simulasi)")
    print("-" * 55)
    dummy_image = b"\xff\xd8\xff" + b"\x00" * 100 + b"\xff\xd9"  # JPEG header simulasi
    enc_img  = encrypt_image(dummy_image)
    dec_img  = decrypt_image(enc_img)
    img_pass = dec_img == dummy_image
    if not img_pass:
        all_passed = False
    print(f"  Original size  : {len(dummy_image)} bytes")
    print(f"  Encrypted size : {len(enc_img)} bytes")
    print(f"  Decrypted match: {'✅ PASS' if img_pass else '❌ FAIL'}")

    # --- 4. Template .env
    print("\n[4] Contoh isi file .env")
    print("-" * 55)
    print(generate_env_template())

    print("=" * 55)
    print(f"  Hasil akhir: {'✅ Semua test PASSED!' if all_passed else '❌ Ada test GAGAL!'}")
    print("=" * 55)
