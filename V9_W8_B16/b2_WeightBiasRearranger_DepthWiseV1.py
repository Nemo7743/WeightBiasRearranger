import os

def process_dw_weights_column_major(weight_file, bias_file, output_folder):
    # 建立輸出資料夾
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 讀取權重與 Bias 檔案
    with open(weight_file, 'r') as fw, open(bias_file, 'r') as fb:
        weight_lines = [line.strip().split() for line in fw if line.strip()]
        bias_lines = [line.strip() for line in fb if line.strip()]

    # 確保處理的組數正確
    num_filters = min(len(weight_lines), len(bias_lines))
    if(len(weight_lines) != len(bias_lines)):
        print("[錯誤]: weight 數量和 bias 數量不匹配")

    print(f"偵測到 {num_filters} 組 DW Filter，開始執行 Column-major 轉換...")

    for i in range(num_filters):
        weights = weight_lines[i]
        bias_hex = bias_lines[i]
        
        # 檢查 3x3 權重是否完整
        if len(weights) < 9:
            print(f"[錯誤]: 第 {i} 組權重不足 9 個，跳過。")
            continue

        # 1. 處理 Bias: 拆分高 2 位與低 2 位 (bias[0:2], bias[2:4])
        bias_high = bias_hex[0:2]
        bias_low = bias_hex[2:4]
        
        output_path_W = os.path.join(output_folder, f"Filter{i}.txt")
        output_path_B = os.path.join(output_folder, f"Bias{i}.txt")
        
        with open(output_path_W, 'w') as f:
            # 寫入權重：轉換為 Column-major 排列
            # 原始索引對應：
            # [0 1 2] -> Row 0
            # [3 4 5] -> Row 1
            # [6 7 8] -> Row 2
            
            # Column 0: 索引 0, 3, 6
            f.write(f"{weights[0]} {weights[3]} {weights[6]} 00\n")
            
            # Column 1: 索引 1, 4, 7
            f.write(f"{weights[1]} {weights[4]} {weights[7]} 00\n")
            
            # Column 2: 索引 2, 5, 8
            f.write(f"{weights[2]} {weights[5]} {weights[8]} 00\n")
        
        with open(output_path_B, 'w') as f:
            # 寫入第一行：Bias 分拆 + Padding
            f.write(f"{bias_high}{bias_low}\n")

    print(f"轉換完成！共生成 {num_filters} 個檔案。")
    print(f"輸出目錄：{os.path.abspath(output_folder)}")

def run_all():
    downSamplingDWLst = [1.0, 2.3]
    originalShuffleDWLst = [2.3]

    for i in range(0, 16):
        if(i==0 or i == 4 or i==12): #------降採樣------
            for j in downSamplingDWLst:
                # 檔案名稱設定
                W_FILE = f"data_model_8_16/features.{i}.banch{j}_w.txt"
                B_FILE = f"data_model_8_16/features.{i}.banch{j}_b.txt"
                output_folder = f"output_data_split/dw_column_filters/features.{i}.banch{j}"

                try:
                    process_dw_weights_column_major(W_FILE, B_FILE, output_folder)
                except FileNotFoundError:
                    print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
                except Exception as e:
                    print(f"發生錯誤：{e}")

        else: #------普通shuffle------
            for j in originalShuffleDWLst:
                # 檔案名稱設定
                W_FILE = f"data_model_8_16/features.{i}.banch{j}_w.txt"
                B_FILE = f"data_model_8_16/features.{i}.banch{j}_b.txt"
                output_folder = f"output_data_split/dw_column_filters/features.{i}.banch{j}"

                try:
                    process_dw_weights_column_major(W_FILE, B_FILE, output_folder)
                except FileNotFoundError:
                    print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
                except Exception as e:
                    print(f"發生錯誤：{e}")

'''
if __name__ == "__main__":
    # 檔案名稱設定
    W_FILE = "data_model/features.0.banch1.0_w.txt"
    B_FILE = "data_model/features.0.banch1.0_b.txt"
    
    try:
        process_dw_weights_column_major(W_FILE, B_FILE)
    except FileNotFoundError:
        print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
    except Exception as e:
        print(f"發生錯誤：{e}")
'''

if __name__ == "__main__":
    downSamplingDWLst = [1.0, 2.3]
    originalShuffleDWLst = [2.3]
    for i in range(0, 16):
        if(i==0 or i == 4 or i==12): #------降採樣------
            for j in downSamplingDWLst:
                # 檔案名稱設定
                W_FILE = f"data_model_8_16/features.{i}.banch{j}_w.txt"
                B_FILE = f"data_model_8_16/features.{i}.banch{j}_b.txt"
                output_folder = f"output_data_split/dw_column_filters/features.{i}.banch{j}"

                try:
                    process_dw_weights_column_major(W_FILE, B_FILE, output_folder)
                except FileNotFoundError:
                    print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
                except Exception as e:
                    print(f"發生錯誤：{e}")

        else: #------普通shuffle------
            for j in originalShuffleDWLst:
                # 檔案名稱設定
                W_FILE = f"data_model_8_16/features.{i}.banch{j}_w.txt"
                B_FILE = f"data_model_8_16/features.{i}.banch{j}_b.txt"
                output_folder = f"output_data_split/dw_column_filters/features.{i}.banch{j}"

                try:
                    process_dw_weights_column_major(W_FILE, B_FILE, output_folder)
                except FileNotFoundError:
                    print("錯誤：找不到指定檔案，請確認檔案放置於同一個資料夾。")
                except Exception as e:
                    print(f"發生錯誤：{e}")
