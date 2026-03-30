# kraken_sdk_py
A Very Simple KrakenSDR Python Interface

# Conda 

```bash
conda create -n kraken python=3.10 -y
conda activate kraken

conda install scipy==1.9.3 -y
conda install numba==0.56.4 -y
conda install configparser -y
conda install pyzmq -y
conda install scikit-rf -y

```

# Example
```bash
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kraken_client import KrakenSDRClient

def run_example():
    # 配置参数
    client = KrakenSDRClient(
        ip_addr="127.0.0.1",
        data_port=5000,
        ctrl_port=5001,
        num_channels=5,
        freq_mhz=416.588,
        gain=[12.5] * 5,  # 使用 valid_gains 中的值
        debug=True
    )

    try:
        print("正在连接 KrakenSDR...")
        client.connect()

        print("正在获取数据帧...")
        iq_data = client.get_data_frame()

        if iq_data is not None:
            print("\n--- 获取成功 ---")
            print(f"数据维度: {iq_data.shape} (通道数 x 采样点)")
            print(f"数据类型: {iq_data.dtype}")
            print(f"第一通道前5个采样点: \n{iq_data[0, :5]}")
            
            # 这里可以添加你自己的处理逻辑，比如 FFT、测向等
            # amplitude = np.abs(iq_data)
        
    except Exception as e:
        print(f"运行出错: {e}")
    finally:
        print("关闭连接...")
        client.close()

if __name__ == "__main__":
    run_example()
```