import os

def process_pw_weights(weight_file, bias_file, output_folder):
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
        print(f"[警告]: Filter 數量 ({num_filters}) 與 Bias 數量 ({num_biases}) 不一致！")
    
    actual_groups = min(num_filters, num_biases)
    print(f"偵測到 {actual_groups} 組 PointWise Filter 資料，開始轉換...")

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
                
                # 如果該層 Channel 數不是 4 的倍數，最後一組需補 00
                while len(chunk) < 4:
                    chunk.append("00")
                
                f.write(f"{' '.join(chunk)}\n")
        
        with open(output_path_B, 'w') as f:
            # 1. 處理 Bias: 拆分高 2 位與低 2 位，並補兩個 00
            # 範例：8d76 -> 8d 76
            bias_high = bias_hex[0:2]
            bias_low = bias_hex[2:4]
            f.write(f"{bias_high}{bias_low}\n")

    print(f"轉換完成！共生成 {actual_groups} 個檔案於 '{output_folder}'。")

def run_all():
    downSamplingPWLst = [1.2, 2.0, 2.5]
    originalShufflePWLst = [2.0, 2.5]
    for i in range(0, 16):
        if(i==0 or i == 4 or i==12): #------降採樣------
            for j in downSamplingPWLst:
                # 檔案名稱設定
                W_FILE = f"data_model_8_16/features.{i}.banch{j}_w.txt"
                B_FILE = f"data_model_8_16/features.{i}.banch{j}_b.txt"
                output_folder = f"output_data_split/pw_column_filters/features.{i}.banch{j}"

                try:
                    process_pw_weights(W_FILE, B_FILE, output_folder)
                except FileNotFoundError:
                    print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
                except Exception as e:
                    print(f"發生錯誤：{e}")

        else: #------普通shuffle------
            for j in originalShufflePWLst:
                # 檔案名稱設定
                W_FILE = f"data_model_8_16/features.{i}.banch{j}_w.txt"
                B_FILE = f"data_model_8_16/features.{i}.banch{j}_b.txt"
                output_folder = f"output_data_split/pw_column_filters/features.{i}.banch{j}"

                try:
                    process_pw_weights(W_FILE, B_FILE, output_folder)
                except FileNotFoundError:
                    print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
                except Exception as e:
                    print(f"發生錯誤：{e}")

'''
if __name__ == "__main__":
    # 設定輸入檔名
    W_FILE = "features.0.banch2.0_w.txt"
    B_FILE = "features.0.banch2.0_b.txt"
    
    try:
        process_pw_weights(W_FILE, B_FILE)
    except FileNotFoundError as e:
        print(f"錯誤：找不到檔案 - {e}")
    except Exception as e:
        print(f"發生非預期錯誤：{e}")
'''

if __name__ == "__main__":
    downSamplingPWLst = [1.2, 2.0, 2.5]
    originalShufflePWLst = [2.0, 2.5]
    for i in range(0, 16):
        if(i==0 or i == 4 or i==12): #------降採樣------
            for j in downSamplingPWLst:
                # 檔案名稱設定
                W_FILE = f"data_model_8_16/features.{i}.banch{j}_w.txt"
                B_FILE = f"data_model_8_16/features.{i}.banch{j}_b.txt"
                output_folder = f"output_data_split/pw_column_filters/features.{i}.banch{j}"

                try:
                    process_pw_weights(W_FILE, B_FILE, output_folder)
                except FileNotFoundError:
                    print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
                except Exception as e:
                    print(f"發生錯誤：{e}")

        else: #------普通shuffle------
            for j in originalShufflePWLst:
                # 檔案名稱設定
                W_FILE = f"data_model_8_16/features.{i}.banch{j}_w.txt"
                B_FILE = f"data_model_8_16/features.{i}.banch{j}_b.txt"
                output_folder = f"output_data_split/pw_column_filters/features.{i}.banch{j}"

                try:
                    process_pw_weights(W_FILE, B_FILE, output_folder)
                except FileNotFoundError:
                    print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
                except Exception as e:
                    print(f"發生錯誤：{e}")