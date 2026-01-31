import os

def process_FC_weights(weight_file, bias_file, output_folder):
    # 建立輸出資料夾
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 讀取權重與 Bias 檔案
    # PW 卷積中，weight_lines 的每一行代表一個 Filter (1x1xC)
    with open(weight_file, 'r') as fw, open(bias_file, 'r') as fb:
        weight_lines = [line.strip().split() for line in fw if line.strip()]
        bias_lines = [line.strip() for line in fb if line.strip()]

    # 檢查 Filter 組數
    num_filters = len(weight_lines)
    num_biases = len(bias_lines)
    
    if num_filters != num_biases:
        print(f"[錯誤]: Filter 數量 ({num_filters}) 與 Bias 數量 ({num_biases}) 不一致！")
    
    actual_groups = min(num_filters, num_biases)
    print(f"偵測到 {actual_groups} 組 FC Filter 資料，開始轉換...")

    for i in range(actual_groups):
        weights = weight_lines[i]
        bias_hex = bias_lines[i]
        
        # 動態計算：這一個 Filter 的通道長度 (Channel Count)
        channel_len = len(weights)
        
        output_path_W = os.path.join(output_folder, f"Filter{i}.txt")
        output_path_B = os.path.join(output_folder, f"Bias{i}.txt")
        
        with open(output_path_W, 'w') as f:
            # 2. 處理權重: 每 4 個權重一組 (對應 64-bit 寬度)
            # 因為是 1x1 卷積，直接照通道順序輸出即可
            for j in range(0, channel_len, 4):
                chunk = weights[j : j + 4]
                
                # 如果該層 Channel 數不是 4 的倍數，最後一組需補 0000
                while len(chunk) < 4:
                    chunk.append("0000")
                
                f.write(f"{' '.join(chunk)}\n")
        
        with open(output_path_B, 'w') as f:
            # 1. 處理 Bias: 拆分高 4 位與低 4 位，並補兩個 0000
            # 範例：ffff8d76 -> ffff 8d76 0000 0000
            bias_high = bias_hex[0:4]
            bias_low = bias_hex[4:8]
            f.write(f"{bias_high}{bias_low}\n")

    print(f"轉換完成！共生成 {actual_groups}*2 個檔案於 '{output_folder}'。")

def run_all():
    # 設定輸入檔名
    W_FILE = "data_model/classifier.1_w.txt"
    B_FILE = "data_model/classifier.1_b.txt"
    output_folder = "output_data_split/fc_filters"
    
    try:
        process_FC_weights(W_FILE, B_FILE, output_folder)
    except FileNotFoundError as e:
        print(f"錯誤：找不到檔案 - {e}")
    except Exception as e:
        print(f"發生非預期錯誤：{e}")

if __name__ == "__main__":
    # 設定輸入檔名
    W_FILE = "data_model/classifier.1_w.txt"
    B_FILE = "data_model/classifier.1_b.txt"
    output_folder = "output_data_split/fc_filters"
    
    try:
        process_FC_weights(W_FILE, B_FILE, output_folder)
    except FileNotFoundError as e:
        print(f"錯誤：找不到檔案 - {e}")
    except Exception as e:
        print(f"發生非預期錯誤：{e}")