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
    if(len(weight_lines) != len(bias_lines)):
        print("[錯誤]: weight 數量和 bias 數量不匹配")

    print(f"開始處理 {num_filters} 組 Filter，轉換為 Column-major 格式...")

    for i in range(num_filters):
        weights = weight_lines[i]
        bias = bias_lines[i]
        
        # 確保權重數量足夠 (3x3x3 = 27)
        if len(weights) < 27:
            print(f"[錯誤]: Filter {i} 權重不足 27 個，略過。")
            continue

        output_path_W = os.path.join(output_folder, f"Filter{i}.txt")
        output_path_B = os.path.join(output_folder, f"Bias{i}.txt")
        
        with open(output_path_W, 'w') as f:
            # 2. 寫入權重行
            # 輸入格式: 每個 Filter 共 27 個權重，依序為 ch1(9個), ch2(9個), ch3(9個)
            # 每個 channel 的 9 個權重排列如下 (flat index k = 0~8):
            #   k=0 k=1 k=2   (Row 0)
            #   k=3 k=4 k=5   (Row 1)
            #   k=6 k=7 k=8   (Row 2)
            #
            # 打包方式: 依 Column-major 順序取 kernel 位置 (0,3,6, 1,4,7, 2,5,8)
            # 對每個位置取三個 channel 同位置的值，合併輸出一行 (共 9 行)
            # 第 k 行格式: ch1[k]  ch2[k]  ch3[k]  0000
            
            ch1 = weights[0:9]
            ch2 = weights[9:18]
            ch3 = weights[18:27]
            
            # Column-major 順序: (0,3,6), (1,4,7), (2,5,8)
            for k in [0, 3, 6, 1, 4, 7, 2, 5, 8]:
                f.write(f"{ch1[k]} {ch2[k]} {ch3[k]} 00\n")
        
        with open(output_path_B, 'w') as f:
            # 1. 寫入 Bias 行
            f.write(f"{bias[0:2]}{bias[2:4]}\n")

    print(f"處理完成！檔案已輸出至: {os.path.abspath(output_folder)}")


def run_all():
    W_FILE = "data_model_8_16/conv1.0_w.txt"
    B_FILE = "data_model_8_16/conv1.0_b.txt"
    output_folder="output_data_split/conv1_column_filters"

    try:
        rearrange_conv1_to_column_major(W_FILE, B_FILE, output_folder)
    except FileNotFoundError:
        print("錯誤：找不到輸入檔案，請檢查檔名是否正確。")
    except Exception as e:
        print(f"發生錯誤：{e}")

if __name__ == "__main__":
    W_FILE = "data_model_8_16/conv1.0_w.txt"
    B_FILE = "data_model_8_16/conv1.0_b.txt"
    output_folder="output_data_split/conv1_column_filters"

    try:
        rearrange_conv1_to_column_major(W_FILE, B_FILE, output_folder)
    except FileNotFoundError:
        print("錯誤：找不到輸入檔案，請檢查檔名是否正確。")
    except Exception as e:
        print(f"發生錯誤：{e}")