import os
import plistlib
import random

def decrypt_payload(data: bytes) -> bytes:
    buf = bytearray(data)
    size = len(buf)
    out_size = (size - 8) // 4
    
    for i in range(size):
        buf[i] ^= (i & 0xFF)
        
    magic1 = buf[2] | (buf[3] << 8)
    magic2 = buf[-4] | (buf[-3] << 8)
    
    if magic1 != 0x6e58 or magic2 != 0xb864:
        raise ValueError("Invalid magic constants.")
        
    val_1e = buf[0] | (buf[1] << 8)
    val_20 = buf[-2] | (buf[-1] << 8)
    
    if (val_1e ^ out_size) != (val_20 ^ 0x38bc):
        raise ValueError("Header checksum mismatch.")
        
    out_buf = bytearray(out_size)
    for i in range(out_size):
        offset = 4 + i * 4
        b0, b1, b2, b3 = buf[offset:offset+4]
        
        mode = b0 & 3
        if mode == 0:
            val, idx = b0 ^ b1, b2 | (b3 << 8)
        elif mode == 1:
            val, idx = b0 ^ b2, b1 | (b3 << 8)
        else: 
            val, idx = b0 ^ b3, b1 | (b2 << 8)
            
        if idx < out_size:
            out_buf[idx] = val
            
    checksum = 0xa961
    for byte in out_buf:
        checksum = (checksum + byte) & 0xFFFF
        
    if (val_1e ^ out_size) != checksum:
        raise ValueError("Data payload checksum mismatch.")
        
    return bytes(out_buf)

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

def unpack_save(plist_path):
    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)
        
    for key in ['profile', 'game_campaign', 'game_custom']:
        if key in plist:
            decrypted = decrypt_payload(plist[key])
            out_path = f"{key}_decrypted.bin"
            with open(out_path, 'wb') as out_f:
                out_f.write(decrypted)
            print(f"Extracted payload to: {out_path}")

def pack_save(original_plist_path, out_plist_path):
    with open(original_plist_path, 'rb') as f:
        plist = plistlib.load(f)
        
    for key in ['profile', 'game_campaign', 'game_custom']:
        in_path = f"{key}_decrypted.bin"
        if os.path.exists(in_path):
            with open(in_path, 'rb') as in_f:
                plaintext = in_f.read()
            plist[key] = encrypt_payload(plaintext)
            print(f"Repacked payload: {key}")
            
    with open(out_plist_path, 'wb') as f:
        plistlib.dump(plist, f, fmt=plistlib.FMT_BINARY)
    print(f"Success. Compiled save to: {out_plist_path}")

# To Unpack: unpack_save("0.plist")
# To Repack: pack_save("0.plist", "modded_0.plist")

if __name__ == "__main__":
    target_file = "1.plist"
    repacked_file = "1_repacked.plist"
    
    print(f"--- Starting Test for {target_file} ---")
    
    if not os.path.exists(target_file):
        print(f"Error: {target_file} not found in the current directory.")
    else:
        print("Unpacking...")
        unpack_save(target_file)
        
        print("\nRepacking...")
        pack_save(target_file, repacked_file)
        
        print("\n--- Test Complete ---")