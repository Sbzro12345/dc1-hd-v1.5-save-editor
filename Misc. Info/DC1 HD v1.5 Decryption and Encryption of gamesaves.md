# This technical documentation outlines the scatter-gather obfuscation and checksum validation used in *Defender Chronicles HD v1.5* save files.

## Payload Architecture

The game stores its variables inside an Apple Binary Property List (`.plist`), specifically within encrypted `NSData` blobs under the keys `profile`, `game_campaign`, and `game_custom`.

The encryption is a deterministic, stateless obfuscation wrapper consisting of three layers:

* **Layer 1 (Sequential XOR):** The entire byte array is masked with a rolling index XOR.
* **Layer 2 (Header/Footer Split):** An 8-byte framing structure validates file integrity, split evenly between the first 4 bytes and the last 4 bytes of the array.
* **Layer 3 (Scatter-Gather Chunks):** Every 1 byte of real plaintext data is expanded into a 4-byte chunk. The chunk self-documents how to decrypt it using a 2-bit mode identifier.

The total size of an encrypted payload is always `(plaintext_size * 4) + 8` bytes.

## Checksum Validation

To prevent save tampering, the game calculates a rolling 16-bit sum of the plaintext data and embeds it into the split header/footer using constant XOR masks.

* **Initial Seed:** The checksum calculation begins with the static constant `0xa961`.
* **Calculation:** `checksum = (checksum + byte) & 0xFFFF` for every byte in the decrypted plaintext.
* **Header Variables:**
* `val_1e` = `checksum ^ plaintext_size`
* `val_20` = `checksum ^ 0x38bc`



### Framing Layout

Once the Outer XOR is removed, the 8 framing bytes sit at the absolute boundaries of the file:

* `buf[0], buf[1]`: `val_1e` (Little-endian)
* `buf[2], buf[3]`: `0x58, 0x6e` (Magic Constant `0x6e58`)
* `buf[-4], buf[-3]`: `0x64, 0xb8` (Magic Constant `0xb864`)
* `buf[-2], buf[-1]`: `val_20` (Little-endian)

## 4-Byte Chunk Protocol

Between the 4-byte header and 4-byte footer sit the payload chunks. Each chunk consists of 4 bytes (`b0, b1, b2, b3`).

`b0` acts as the instruction manual for the chunk. The lowest 2 bits of `b0` (`b0 & 0x3`) determine the "Mode" (0, 1, 2, or 3). The Mode dictates which of the remaining three bytes holds the XOR-scrambled data, and which two bytes hold the 16-bit little-endian coordinate (the original index) for that data.

* **Mode 0:**
* Scrambled Data = `b1`
* Coordinate = `b2 | (b3 << 8)`


* **Mode 1:**
* Scrambled Data = `b2`
* Coordinate = `b1 | (b3 << 8)`


* **Modes 2 and 3:**
* Scrambled Data = `b3`
* Coordinate = `b1 | (b2 << 8)`



The real data byte is always extracted by XORing the scrambled data byte against `b0` (e.g., `Real_Data = Scrambled_Data ^ b0`).

## Decryption Procedure

1. **Remove Outer XOR:** Iterate through the entire encrypted byte array. For each byte at index `i`, apply `buf[i] ^= (i & 0xFF)`.
2. **Validate Magic Numbers:** Extract the 16-bit little-endian integers at offsets `2` and `size - 4`. If they do not equal `0x6e58` and `0xb864` respectively, abort decryption.
3. **Calculate Plaintext Size:** `out_size = (total_encrypted_size - 8) / 4`. Allocate an empty byte array of this size.
4. **Parse Chunks:** Loop through the buffer in 4-byte steps, starting at offset `4` and ending at `size - 4`.
5. **Extract Data:** For each chunk, read `b0` to determine the Mode. Extract the original index and the scrambled data byte based on the Mode rules above.
6. **Unscramble & Place:** Calculate `val = Scrambled_Data ^ b0`. Place `val` into the allocated plaintext array at the extracted original index.
7. **Verify Checksum:** Calculate the rolling sum of the resulting plaintext starting from `0xa961`. Read `val_1e` from `buf[0], buf[1]`. If `(val_1e ^ out_size) != calculated_checksum`, the data is corrupted.

## Encryption Procedure

1. **Calculate Plaintext Properties:** Determine the `out_size` (length of the plaintext) and generate the rolling 16-bit checksum starting from `0xa961`.
2. **Allocate Buffer:** Create an empty byte array of size `(out_size * 4) + 8`.
3. **Write Framing:** Calculate `val_1e` and `val_20`. Write the 8 framing bytes to the start and end of the allocated buffer as detailed in the Framing Layout.
4. **Shuffle Indices:** Create an array of integers from `0` to `out_size - 1` and randomly shuffle it. This array dictates the randomized physical order the chunks will be written in.
5. **Encode Chunks:** For every byte in the plaintext:
* Pick a random Mode (0 to 3).
* Generate a random 6-bit integer, shift it left by 2, and bitwise OR it with the Mode to create `b0` (`b0 = (rand(0, 63) << 2) | Mode`).
* Scramble the data byte: `Scrambled_Data = plaintext_byte ^ b0`.
* Format `b1, b2, b3` using the Scrambled Data and the byte's actual original index, following the reverse of the Mode rules.
* Write the 4 bytes into the allocated buffer at the offset determined by the shuffled index array (`4 + (shuffled_index * 4)`).


6. **Apply Outer XOR:** Iterate through the entire buffer. For each byte at index `i`, apply `buf[i] ^= (i & 0xFF)`. The payload is now ready to be written to the `.plist`.