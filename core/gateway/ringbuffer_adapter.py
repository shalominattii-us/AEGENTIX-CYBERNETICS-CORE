"""
Python Shared-Memory Ring Buffer Adapter
========================================
Bridges Python gateway / agents with bare-metal C runtime inference engines
via memory-mapped circular ring buffer with zero-copy binary framing.
"""

from __future__ import annotations
import os
import mmap
import time
import struct
from typing import Optional, Tuple, Generator

RINGBUFFER_MAGIC = 0x41454758  # "AEGX"
RINGBUFFER_VERSION = 1
HEADER_FORMAT = "<IIIIII10I"  # 16 uint32_t fields = 64 bytes
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MSG_HEADER_FORMAT = "<III"   # msg_type, payload_len, checksum = 12 bytes
MSG_HEADER_SIZE = struct.calcsize(MSG_HEADER_FORMAT)

# Message types
MSG_TYPE_HEARTBEAT = 0x0001
MSG_TYPE_INFER_REQ = 0x0002
MSG_TYPE_TOKEN     = 0x0003
MSG_TYPE_EOS       = 0x0004
MSG_TYPE_ERROR     = 0x0005


def _calculate_checksum(data: bytes) -> int:
    s = 0
    for b in data:
        s = ((s * 31) + b) & 0xFFFFFFFF
    return s


class RingBufferAdapter:
    """
    Python interface to the shared-memory circular ring buffer.
    Compatible with Windows Win32 file mapping tags and POSIX mmap.
    """

    def __init__(
        self,
        name: str = "aegentix_ipc_ringbuf",
        capacity: int = 1024 * 1024,
        create: bool = False
    ):
        self.name = name
        self.capacity = capacity
        self.total_size = HEADER_SIZE + capacity
        self.create = create
        self._mmap: Optional[mmap.mmap] = None

        if create:
            self._create_or_open_shm()
        else:
            self._open_shm()

    def _create_or_open_shm(self) -> None:
        """Create or open named shared memory segment."""
        # On Windows, mmap.mmap(-1, size, tagname=name) creates/opens named shared memory
        self._mmap = mmap.mmap(-1, self.total_size, tagname=self.name, access=mmap.ACCESS_WRITE)
        # Initialize header if empty / brand new
        self._mmap.seek(0)
        existing_magic = struct.unpack("<I", self._mmap.read(4))[0]
        if existing_magic != RINGBUFFER_MAGIC:
            self._mmap.seek(0)
            header_bytes = struct.pack(
                HEADER_FORMAT,
                RINGBUFFER_MAGIC,
                RINGBUFFER_VERSION,
                self.capacity,
                0,  # head
                0,  # tail
                1,  # flags: active
                *[0] * 10
            )
            self._mmap.write(header_bytes)

    def _open_shm(self) -> None:
        """Attach to an existing named shared memory segment."""
        try:
            self._mmap = mmap.mmap(-1, self.total_size, tagname=self.name, access=mmap.ACCESS_WRITE)
        except Exception:
            # Fallback to create if not present
            self._create_or_open_shm()

    def _read_header(self) -> Tuple[int, int, int, int, int, int]:
        """Returns (magic, version, capacity, head, tail, flags)."""
        self._mmap.seek(0)
        raw = self._mmap.read(HEADER_SIZE)
        unpacked = struct.unpack(HEADER_FORMAT, raw)
        return unpacked[0], unpacked[1], unpacked[2], unpacked[3], unpacked[4], unpacked[5]

    def _write_pointers(self, head: Optional[int] = None, tail: Optional[int] = None) -> None:
        if head is not None:
            self._mmap.seek(12)  # offset of head in header
            self._mmap.write(struct.pack("<I", head))
        if tail is not None:
            self._mmap.seek(16)  # offset of tail in header
            self._mmap.write(struct.pack("<I", tail))

    def push(self, msg_type: int, payload: bytes) -> bool:
        """Pushes a message with header and checksum into the circular buffer."""
        magic, ver, cap, head, tail, flags = self._read_header()
        if magic != RINGBUFFER_MAGIC:
            return False

        needed = MSG_HEADER_SIZE + len(payload)
        used = (head - tail) if (head >= tail) else (cap - (tail - head))
        free_space = cap - used - 1

        if needed > free_space:
            return False  # Buffer full

        checksum = _calculate_checksum(payload)
        mhdr = struct.pack(MSG_HEADER_FORMAT, msg_type, len(payload), checksum)

        # Write msg header
        cur_head = head
        data_to_write = mhdr + payload
        data_len = len(data_to_write)

        buf_offset = HEADER_SIZE
        if cur_head + data_len <= cap:
            self._mmap.seek(buf_offset + cur_head)
            self._mmap.write(data_to_write)
            cur_head = (cur_head + data_len) % cap
        else:
            first_part = cap - cur_head
            self._mmap.seek(buf_offset + cur_head)
            self._mmap.write(data_to_write[:first_part])
            self._mmap.seek(buf_offset)
            self._mmap.write(data_to_write[first_part:])
            cur_head = data_len - first_part

        self._write_pointers(head=cur_head)
        return True

    def pop(self) -> Optional[Tuple[int, bytes]]:
        """Pops the next available message. Returns (msg_type, payload) or None."""
        magic, ver, cap, head, tail, flags = self._read_header()
        if head == tail:
            return None

        used = (head - tail) if (head >= tail) else (cap - (tail - head))
        if used < MSG_HEADER_SIZE:
            return None

        buf_offset = HEADER_SIZE
        cur_tail = tail

        # Read msg header
        if cur_tail + MSG_HEADER_SIZE <= cap:
            self._mmap.seek(buf_offset + cur_tail)
            hdr_bytes = self._mmap.read(MSG_HEADER_SIZE)
            cur_tail = (cur_tail + MSG_HEADER_SIZE) % cap
        else:
            first = cap - cur_tail
            self._mmap.seek(buf_offset + cur_tail)
            part1 = self._mmap.read(first)
            self._mmap.seek(buf_offset)
            part2 = self._mmap.read(MSG_HEADER_SIZE - first)
            hdr_bytes = part1 + part2
            cur_tail = MSG_HEADER_SIZE - first

        msg_type, payload_len, checksum = struct.unpack(MSG_HEADER_FORMAT, hdr_bytes)
        if used < (MSG_HEADER_SIZE + payload_len):
            return None  # Partial payload

        # Read payload
        if cur_tail + payload_len <= cap:
            self._mmap.seek(buf_offset + cur_tail)
            payload = self._mmap.read(payload_len)
            cur_tail = (cur_tail + payload_len) % cap
        else:
            first = cap - cur_tail
            self._mmap.seek(buf_offset + cur_tail)
            part1 = self._mmap.read(first)
            self._mmap.seek(buf_offset)
            part2 = self._mmap.read(payload_len - first)
            payload = part1 + part2
            cur_tail = payload_len - first

        # Checksum verification
        if _calculate_checksum(payload) != checksum:
            self._write_pointers(tail=cur_tail)
            raise ValueError("Corrupted message checksum in ring buffer")

        self._write_pointers(tail=cur_tail)
        return msg_type, payload

    def stream_tokens(self, timeout_s: float = 5.0) -> Generator[str, None, None]:
        """Generator that streams tokens until EOS or timeout."""
        start = time.time()
        while time.time() - start < timeout_s:
            item = self.pop()
            if item is None:
                time.sleep(0.001)
                continue
            msg_type, payload = item
            if msg_type == MSG_TYPE_TOKEN:
                yield payload.decode("utf-8", errors="replace")
            elif msg_type == MSG_TYPE_EOS:
                break
            elif msg_type == MSG_TYPE_ERROR:
                err_msg = payload.decode("utf-8", errors="replace")
                raise RuntimeError(f"Edge C Runner Error: {err_msg}")

    def close(self) -> None:
        if self._mmap is not None:
            self._mmap.close()
            self._mmap = None
