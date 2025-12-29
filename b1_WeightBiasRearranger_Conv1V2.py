import os

def rearrange_conv1_to_column_major(weight_file, bias_file, output_folder):
    # 建立輸出資料夾
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 讀取權重與 Bias
    with open(weight_file, 'r') as fw, open(bias_file, 'r') as fb:
        weight_lines = [line.strip().split() for line in fw if line.strip()]
        bias_lines = [line.strip() for line in fb if line.strip()]

    num_filters = min(len(weight_lines), len(bias_lines))
    print(f"開始處理 {num_filters} 組 Filter，轉換為 Column-major 格式...")

    for i in range(num_filters):
        weights = weight_lines[i]
        bias = bias_lines[i]
        
        # 確保權重數量足夠 (3x3x3 = 27)
        if len(weights) < 27:
            print(f"警告：Filter {i} 權重不足 27 個，略過。")
            continue

        output_path = os.path.join(output_folder, f"Filter{i}.txt")
        
        with open(output_path, 'w') as f:
            # 1. 寫入 Bias 行: bias0 bias0 0000 0000
            f.write(f"{bias[0:4]} {bias[4:8]} 0000 0000\n")
            
            # 2. 寫入權重行 (Column-major 排列)
            # 每 9 個權重為一個 Channel (共 3 個 Channel)
            for channel_offset in range(0, 27, 9):
                # 取得目前 Channel 的 9 個權重
                # 索引對應:
                # 0 1 2 (Row 0)
                # 3 4 5 (Row 1)
                # 6 7 8 (Row 2)
                # 轉換為 Column 輸出: (0,3,6), (1,4,7), (2,5,8)
                
                ch_w = weights[channel_offset : channel_offset + 9]
                
                # Column 0: Index 0, 3, 6
                f.write(f"{ch_w[0]} {ch_w[3]} {ch_w[6]} 0000\n")
                # Column 1: Index 1, 4, 7
                f.write(f"{ch_w[1]} {ch_w[4]} {ch_w[7]} 0000\n")
                # Column 2: Index 2, 5, 8
                f.write(f"{ch_w[2]} {ch_w[5]} {ch_w[8]} 0000\n")

    print(f"處理完成！檔案已輸出至: {os.path.abspath(output_folder)}")

def run_all():
    W_FILE = "data_model/conv1.0_w.txt"
    B_FILE = "data_model/conv1.0_b.txt"
    output_folder="output_data/conv1_column_filters"

    try:
        rearrange_conv1_to_column_major(W_FILE, B_FILE, output_folder)
    except FileNotFoundError:
        print("錯誤：找不到輸入檔案，請檢查檔名是否正確。")
    except Exception as e:
        print(f"發生錯誤：{e}")

if __name__ == "__main__":
    W_FILE = "data_model/conv1.0_w.txt"
    B_FILE = "data_model/conv1.0_b.txt"
    output_folder="output_data/conv1_column_filters"

    try:
        rearrange_conv1_to_column_major(W_FILE, B_FILE, output_folder)
    except FileNotFoundError:
        print("錯誤：找不到輸入檔案，請檢查檔名是否正確。")
    except Exception as e:
        print(f"發生錯誤：{e}")