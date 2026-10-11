"""Assemble synthetic archives without distributing original game assets."""
import struct

from rt3_ultrawide import loading, menu


def combined_archive():
    directory, payload, offset = [], [], 0
    for data in [menu.archive_bytes(), loading.archive_bytes()]:
        _, count = struct.unpack_from("<II", data)
        base = 8 + 74 * count
        for i in range(count):
            key, size, start, flag, name = struct.unpack_from("<IIIB61s", data, 8 + 74 * i)
            directory.append(struct.pack("<IIIB61s", key, size, offset, flag, name))
            payload.append(data[base + start:base + start + size])
            offset += size
    return struct.pack("<II", 1003, len(directory)) + b"".join(directory + payload)
