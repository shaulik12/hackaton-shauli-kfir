import struct
byteMsg = struct.pack('LbH', 0xabcddcba, 0x2, 7562)
print(byteMsg)