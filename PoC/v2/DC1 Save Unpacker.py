import os
import plistlib

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

if __name__ == "__main__":
    target_file = input("Enter the filename to unpack (e.g., 1.plist): ").strip()
    
    print(f"\n--- Starting Unpack for {target_file} ---")
    
    if not os.path.exists(target_file):
        print(f"Error: '{target_file}' not found in the current directory.")
    else:
        unpack_save(target_file)
        print("--- Unpack Complete ---")
        
    input("\nPress Enter to exit...")