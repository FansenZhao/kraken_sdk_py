#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from krakensdr import KrakenSDRClient

if __name__ == "__main__":
    client = KrakenSDRClient(
        ip_addr="127.0.0.1",
        data_port=5000,
        ctrl_port=5001,
        num_channels=5,
        freq_mhz=416.588,
        gain=12.5,   # 这里只输入一个数，5个通道自动相同
        debug=True,
    )

    try:
        client.connect()

        iq = client.get_data_frame()

        print("IQ shape:", iq.shape)
        print("IQ dtype:", iq.dtype)
        print("Current gain setting:", client.gain)
        print("Header center freq:", client.iq_header.rf_center_freq)
        print("Header sampling freq:", client.iq_header.sampling_freq)

        print("CH0 first 10 samples:")
        print(iq[0, :10])

        # 运行过程中也可以动态修改成所有通道相同 gain
        # client.set_if_gain(20.7)

    finally:
        client.close()