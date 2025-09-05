from pathlib import Path

ROOT = Path("C:/Users/DELL/OneDrive - Swinburne University/Documents/GitHub/HIT137/Question 1/raw_text.txt").parent
RAW = ROOT / "raw_text.txt"
ENC = ROOT / "encrypted_text.txt"
DEC = ROOT / "decrypted_text.txt"

def shift(ch, k):
    """Shift a letter by k positions, wrapping A-Z/a-z."""
    if ch.isalpha():
        base = ord('a') if ch.islower() else ord('A')
        new_ch = chr(base + ((ord(ch) - base + k) % 26))
        print(f"Shifting {ch} by {k} -> {new_ch}")  # Debug line
        return new_ch
    return ch

def enc_char(ch, s1, s2):
    """Encrypt a single character based on the shift rules."""
    if ch.islower():
        print(f"Encrypting lowercase {ch}")
        return shift(ch, (s1 * s2)) if ch <= 'm' else shift(ch, -(s1 + s2))
    if ch.isupper():
        print(f"Encrypting uppercase {ch}")
        return shift(ch, -(s1)) if ch <= 'M' else shift(ch, (s2 * s2))
    return ch

def dec_char(ch, s1, s2):
    """Decrypt a single character, checking the correct half for each letter."""
    if ch.islower():
        k1, k2 = (s1 * s2), (s1 + s2)
        print(f"Decrypting lowercase {ch}")
        p1, p2 = shift(ch, -k1), shift(ch, +k2)  # assume original was a–m or n–z
        return p1 if ('a' <= p1 <= 'm') else (p2 if 'n' <= p2 <= 'z' else p1)
    if ch.isupper():
        kA, kB = s1, (s2 * s2)
        print(f"Decrypting uppercase {ch}")
        p1, p2 = shift(ch, +kA), shift(ch, -kB)  # assume original was A–M or N–Z
        return p1 if ('A' <= p1 <= 'M') else (p2 if 'N' <= p2 <= 'Z' else p1)
    return ch

def transform(text, s1, s2, mode):
    """Apply encryption or decryption over the entire text."""
    f = enc_char if mode == "encrypt" else dec_char
    return "".join(f(ch, s1, s2) for ch in text)

def first_diff(a, b):
    """Find the first difference between two strings."""
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else -1

def main():
    print("=== Q1: Encrypt → Decrypt → Verify ===")
    s1 = int(input("Enter shift1 (integer): ").strip())
    s2 = int(input("Enter shift2 (integer): ").strip())

    # Encrypt raw → ENC
    raw = RAW.read_text(encoding="utf-8").strip()
    ENC.write_text(transform(raw, s1, s2, "encrypt"), encoding="utf-8")

    # Decrypt ENC → DEC
    enc = ENC.read_text(encoding="utf-8").strip()
    DEC.write_text(transform(enc, s1, s2, "decrypt"), encoding="utf-8")

    # Verify files (ignore trailing whitespace)
    dec = DEC.read_text(encoding="utf-8").strip()
    raw = raw.strip()

    if raw == dec:
        print("Decryption successful: files match ✅")
    else:
        i = first_diff(raw, dec)
        print("Decryption failed: files differ ❌")
        if i >= 0:
            # show the difference
            a = raw[max(0, i-10): i+10].replace("\n", "\\n")
            b = dec[max(0, i-10): i+10].replace("\n", "\\n")
            print(f"First difference at index {i}:")
            print(f"  raw: …{a}…")
            print(f"  dec: …{b}…")

if __name__ == "__main__":
    main()
