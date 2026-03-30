#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import numpy as np
from struct import pack, unpack


class IQHeader:
    FRAME_TYPE_DATA = 0
    FRAME_TYPE_DUMMY = 1
    FRAME_TYPE_RAMP = 2
    FRAME_TYPE_CAL = 3
    FRAME_TYPE_TRIGW = 4
    SYNC_WORD = 0x2BF7B95A

    def __init__(self):
        self.header_size = 1024
        self.reserved_bytes = 192

        self.sync_word = self.SYNC_WORD
        self.frame_type = 0
        self.hardware_id = ""
        self.unit_id = 0
        self.active_ant_chs = 0
        self.ioo_type = 0
        self.rf_center_freq = 0
        self.adc_sampling_freq = 0
        self.sampling_freq = 0
        self.cpi_length = 0
        self.time_stamp = 0
        self.daq_block_index = 0
        self.cpi_index = 0
        self.ext_integration_cntr = 0
        self.data_type = 0
        self.sample_bit_depth = 0
        self.adc_overdrive_flags = 0
        self.if_gains = [0] * 32
        self.delay_sync_flag = 0
        self.iq_sync_flag = 0
        self.sync_state = 0
        self.noise_source_state = 0
        self.header_version = 0

    def decode_header(self, iq_header_byte_array):
        fmt = "II16sIIIQQQIQIIQIII" + "I" * 32 + "IIII" + "I" * self.reserved_bytes + "I"
        iq_header_list = unpack(fmt, iq_header_byte_array)

        self.sync_word = iq_header_list[0]
        self.frame_type = iq_header_list[1]
        self.hardware_id = iq_header_list[2].decode(errors="ignore").rstrip("\x00")
        self.unit_id = iq_header_list[3]
        self.active_ant_chs = iq_header_list[4]
        self.ioo_type = iq_header_list[5]
        self.rf_center_freq = iq_header_list[6]
        self.adc_sampling_freq = iq_header_list[7]
        self.sampling_freq = iq_header_list[8]
        self.cpi_length = iq_header_list[9]
        self.time_stamp = iq_header_list[10]
        self.daq_block_index = iq_header_list[11]
        self.cpi_index = iq_header_list[12]
        self.ext_integration_cntr = iq_header_list[13]
        self.data_type = iq_header_list[14]
        self.sample_bit_depth = iq_header_list[15]
        self.adc_overdrive_flags = iq_header_list[16]
        self.if_gains = list(iq_header_list[17:49])
        self.delay_sync_flag = iq_header_list[49]
        self.iq_sync_flag = iq_header_list[50]
        self.sync_state = iq_header_list[51]
        self.noise_source_state = iq_header_list[52]
        self.header_version = iq_header_list[52 + self.reserved_bytes + 1]

    def dump_header(self):
        print(f"--- IQ Header Info ---")
        print(f"Sync word: {self.sync_word} | Version: {self.header_version}")
        print(f"Frame type: {self.frame_type} | Unit ID: {self.unit_id}")
        print(f"RF Freq: {self.rf_center_freq / 1e6:.2f} MHz | IQ Freq: {self.sampling_freq / 1e6:.2f} MHz")
        print(f"Channels: {self.active_ant_chs} | CPI Length: {self.cpi_length}")
        print(f"Sample bit depth: {self.sample_bit_depth}")
        print(f"----------------------")


class KrakenSDRClient:
    def __init__(
        self,
        ip_addr="127.0.0.1",
        data_port=5000,
        ctrl_port=5001,
        num_channels=5,
        freq_mhz=416.588,
        gain=10.0,
        debug=False,
        timeout=5.0
    ):
        self.ip_addr = ip_addr
        self.data_port = data_port
        self.ctrl_port = ctrl_port
        self.num_channels = num_channels
        self.freq_hz = int(freq_mhz * 1e6)
        self.debug = debug
        self.timeout = timeout

        self.valid_gains = [
            0, 0.9, 1.4, 2.7, 3.7, 7.7, 8.7, 12.5, 14.4, 15.7,
            16.6, 19.7, 20.7, 22.9, 25.4, 28.0, 29.7, 32.8, 33.8,
            36.4, 37.2, 38.6, 40.2, 42.1, 43.4, 43.9, 44.5, 48.0, 49.6
        ]

        self.iq_header = IQHeader()
        self.data_socket = None
        self.ctrl_socket = None
        self.connected = False
        self.ctrl_lock = threading.Lock()

        self.gain = self._normalize_gain(gain)

    def _normalize_gain(self, gain):
        """
        支持两种输入：
        1. 单个数字，例如 12.5 -> [12.5, 12.5, 12.5, 12.5, 12.5]
        2. 列表，例如 [12.5, 12.5, 12.5, 12.5, 12.5]
        """
        if gain is None:
            return [10.0] * self.num_channels

        if isinstance(gain, (int, float)):
            return [float(gain)] * self.num_channels

        if isinstance(gain, (list, tuple)):
            if len(gain) != self.num_channels:
                raise ValueError(f"gain list length must be {self.num_channels}")
            return [float(g) for g in gain]

        raise TypeError("gain must be a number or a list/tuple of numbers")

    def connect(self):
        if self.connected:
            return

        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket.settimeout(self.timeout)
        self.data_socket.connect((self.ip_addr, self.data_port))
        self.data_socket.sendall(b"streaming")

        self.ctrl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ctrl_socket.settimeout(self.timeout)
        self.ctrl_socket.connect((self.ip_addr, self.ctrl_port))

        self.connected = True

        self._send_control_command(b"INIT" + bytearray(124))
        self.set_center_freq(self.freq_hz)
        self.set_if_gain(self.gain)

    def close(self):
        try:
            if self.data_socket is not None:
                try:
                    self.data_socket.sendall(b"q")
                except Exception:
                    pass
                self.data_socket.close()
        finally:
            self.data_socket = None

        try:
            if self.ctrl_socket is not None:
                try:
                    self.ctrl_socket.sendall(b"EXIT" + bytearray(124))
                except Exception:
                    pass
                self.ctrl_socket.close()
        finally:
            self.ctrl_socket = None

        self.connected = False

    def _send_control_command(self, msg_bytes):
        if not self.connected:
            raise RuntimeError("KrakenSDR is not connected")

        with self.ctrl_lock:
            self.ctrl_socket.sendall(msg_bytes)
            reply = self._recv_exact(self.ctrl_socket, 128)

        status = reply[:4].decode(errors="ignore")
        if status != "FNSD":
            raise RuntimeError(f"Control command failed, reply={status}")

    def set_center_freq(self, freq_hz):
        if not self.connected:
            raise RuntimeError("KrakenSDR is not connected")

        self.freq_hz = int(freq_hz)
        cmd = b"FREQ" + pack("Q", self.freq_hz) + bytearray(116)
        self._send_control_command(cmd)

    def set_if_gain(self, gain):
        """
        支持：
        client.set_if_gain(12.5)
        或
        client.set_if_gain([12.5, 12.5, 12.5, 12.5, 12.5])
        """
        if not self.connected:
            raise RuntimeError("KrakenSDR is not connected")

        gain_list = self._normalize_gain(gain)
        self.gain = gain_list

        clipped = []
        for g in gain_list:
            closest = min(self.valid_gains, key=lambda x: abs(x - g))
            clipped.append(int(round(closest * 10)))

        cmd = b"GAIN" + pack("I" * self.num_channels, *clipped)
        cmd += bytearray(128 - (self.num_channels + 1) * 4)
        self._send_control_command(cmd)

    def _recv_exact(self, sock, nbytes):
        buf = bytearray(nbytes)
        view = memoryview(buf)
        received = 0

        while received < nbytes:
            n = sock.recv_into(view, nbytes - received)
            if n == 0:
                raise ConnectionError("Socket connection closed")
            view = view[n:]
            received += n

        return bytes(buf)

    def receive_iq_frame(self):
        if not self.connected:
            raise RuntimeError("KrakenSDR is not connected")

        header_bytes = self._recv_exact(self.data_socket, self.iq_header.header_size)
        self.iq_header.decode_header(header_bytes)

        if self.debug:
            self.iq_header.dump_header()

        payload_size = (
            self.iq_header.cpi_length
            * self.iq_header.active_ant_chs
            * 2
            * int(self.iq_header.sample_bit_depth / 8)
        )

        if payload_size <= 0:
            return None

        payload = self._recv_exact(self.data_socket, payload_size)

        iq = np.frombuffer(payload, dtype=np.complex64).reshape(
            self.iq_header.active_ant_chs,
            self.iq_header.cpi_length
        )
        return iq

    def get_iq_once(self):
        if not self.connected:
            self.connect()

        self.data_socket.sendall(b"IQDownload")
        return self.receive_iq_frame()

    def get_data_frame(self, max_retry=20):
        """
        连续请求直到拿到 DATA 帧
        """
        if not self.connected:
            self.connect()

        for _ in range(max_retry):
            self.data_socket.sendall(b"IQDownload")
            iq = self.receive_iq_frame()
            if self.iq_header.frame_type == IQHeader.FRAME_TYPE_DATA:
                return iq

        raise RuntimeError("Failed to get DATA frame within max_retry")
