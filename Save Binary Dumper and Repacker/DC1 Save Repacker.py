import os
import plistlib
import random

def encrypt_payload(plaintext: bytes) -> bytes:
    out_size = len(plaintext)
    size = out_size * 4 + 8
    buf = bytearray(size)
    
    checksum = 0xa961
    for byte in plaintext:
        checksum = (checksum + byte) & 0xFFFF
        
    val_1e = checksum ^ out_size
    val_20 = checksum ^ 0x38bc
    
    buf[0], buf[1] = val_1e & 0xFF, (val_1e >> 8) & 0xFF
    buf[2], buf[3] = 0x58, 0x6e
    buf[-4], buf[-3] = 0x64, 0xb8
    buf[-2], buf[-1] = val_20 & 0xFF, (val_20 >> 8) & 0xFF
    
    chunk_indices = list(range(out_size))
    random.shuffle(chunk_indices) 
    
    for orig_idx, val in enumerate(plaintext):
        offset = 4 + chunk_indices[orig_idx] * 4
        mode = random.randint(0, 3)
        b0 = (random.randint(0, 63) << 2) | mode
        
        if mode == 0:
            b1, b2, b3 = b0 ^ val, orig_idx & 0xFF, (orig_idx >> 8) & 0xFF
        elif mode == 1:
            b2, b1, b3 = b0 ^ val, orig_idx & 0xFF, (orig_idx >> 8) & 0xFF
        else:
            b3, b1, b2 = b0 ^ val, orig_idx & 0xFF, (orig_idx >> 8) & 0xFF
            
        buf[offset:offset+4] = [b0, b1, b2, b3]
        
    for i in range(size):
        buf[i] ^= (i & 0xFF)
        
    return bytes(buf)

def pack_save_from_scratch(out_plist_path):
    plist_dict = {}
    
    for key in ['profile', 'game_campaign', 'game_custom']:
        in_path = f"{key}_decrypted.bin"
        if os.path.exists(in_path):
            with open(in_path, 'rb') as in_f:
                plaintext = in_f.read()
            plist_dict[key] = encrypt_payload(plaintext)
            print(f"Packed payload: {key}")
        else:
            print(f"Warning: {in_path} not found. Skipping.")
            
    if not plist_dict:
        print("Error: No decrypted .bin files found to pack.")
        return
        
    with open(out_plist_path, 'wb') as f:
        plistlib.dump(plist_dict, f, fmt=plistlib.FMT_BINARY)
    print(f"Success. Compiled standalone save to: {out_plist_path}")

if __name__ == "__main__":
    repacked_file = "com.chillingo.defenderchronicleshd.plist"
        
    print("\nRepacking from scratch...")
    pack_save_from_scratch(repacked_file)
    print("\n--- Repacking Complete ---")
    input()