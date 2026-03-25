import pandas as pd
import re
import math
import os

def parse_isa_to_bin(file_path, output_path):
    # --- 檢查檔案是否存在 ---
    if not os.path.exists(file_path):
        return f"錯誤: 找不到檔案 {file_path}"

    # --- 讀取 Excel ---
    try:
        # header=None 確保第一列也是數據的一部分
        df = pd.read_excel(file_path, header=None, dtype=str, engine='openpyxl')
    except ImportError:
        return "錯誤: 缺少套件。請執行 `pip install openpyxl`"
    except Exception as e:
        return f"讀取檔案失敗: {e}"

    # 定義區塊順序
    block_order = ['OP_Code', 'Core', 'TBO', 'NoC', 'PreP']
    
    # 1. 尋找定義區塊的起始欄位 (OP_Code 在哪一欄)
    start_col_idx = 11
    found_start = False
    
    # 安全檢查: 避免 Excel 空白欄位造成 IndexError
    check_cols = min(len(df.columns), 50) 
    
    # 掃描第一列尋找 Header 位置
    for col in range(check_cols):
        val = str(df.iloc[0, col]).strip()
        if val == 'OP_Code':
            start_col_idx = col
            found_start = True
            break
    
    if not found_start:
        return "錯誤: 無法在第一列找到 'OP_Code' 定義標記"

    # 2. 解析 Schema (訊號位寬定義)
    temp_schema = {b: [] for b in block_order}
    
    for row_idx, block_name in enumerate(block_order):
        for col_idx in range(start_col_idx + 1, len(df.columns)):
            cell_val = str(df.iloc[row_idx, col_idx]).strip()
            
            if pd.isna(df.iloc[row_idx, col_idx]) or cell_val == '' or cell_val.lower() == 'nan':
                continue
                
            match = re.match(r"(.+)\[(\d+)\]", cell_val)
            if match:
                signal_name = match.group(1).strip()
                bits = int(match.group(2))
                temp_schema[block_name].append({
                    'name': signal_name,
                    'bits': bits,
                    'col_idx': col_idx,
                    'row_offset': row_idx
                })
    
    final_signal_order = []
    for block in block_order:
        final_signal_order.extend(temp_schema[block])

    # 3. 處理指令數據
    bin_outputs = []  # 儲存最終的二進制字串
    num_rows = len(df)
    
    # 找出所有指令區塊的起始列
    instruction_start_rows = []
    for r in range(num_rows):
        val = str(df.iloc[r, start_col_idx]).strip()
        if val == 'OP_Code':
            instruction_start_rows.append(r)
            
    if instruction_start_rows and instruction_start_rows[0] == 0:
        instruction_start_rows.pop(0)

    print(f"偵測到 {len(instruction_start_rows)} 條指令區塊。")

    # 針對每一個找到的起始列進行解析
    for base_row in instruction_start_rows:
        instruction_bin_str = ""
        
        block_label = str(df.iloc[base_row, start_col_idx]).strip()
        if block_label != 'OP_Code':
            continue

        for signal in final_signal_order:
            target_row = base_row + signal['row_offset']
            target_col = signal['col_idx']
            
            if target_row >= num_rows or target_col >= len(df.columns):
                raw_val = float('nan') # 標記為空
            else:
                raw_val = df.iloc[target_row, target_col]
                
            val_str = str(raw_val).strip()
            
            # --- [修改 2] 遇到空白儲存格就跳過 ---
            # 判斷是否為真正的空白 (None, NaN, 空字串)
            if pd.isna(raw_val) or val_str == '' or val_str.lower() == 'nan':
                continue # 跳過此次迴圈，不產生任何 Bit

            parsed_int_val = 0
            
            # 判斷 'X' (視為 0)
            if val_str.upper() == 'X':
                parsed_int_val = 0
            
            # TBO 處理 (Hex 轉 Bin)
            elif '_' in val_str and signal['row_offset'] == 2:
                clean_str = val_str.replace('_', '')
                tbo_bits_str = ""
                for i, char in enumerate(clean_str):
                    try:
                        digit_val = int(char, 16)
                        width = 2 if i == len(clean_str) - 1 else 3
                        tbo_bits_str += f"{digit_val:0{width}b}"
                    except ValueError:
                        width = 2 if i == len(clean_str) - 1 else 3
                        tbo_bits_str += "0" * width

                if len(tbo_bits_str) < signal['bits']:
                    tbo_bits_str = tbo_bits_str.zfill(signal['bits'])
                elif len(tbo_bits_str) > signal['bits']:
                    tbo_bits_str = tbo_bits_str[-signal['bits']:]
                
                instruction_bin_str += tbo_bits_str
                continue 

            # OP_Code 處理
            elif signal['row_offset'] == 0:
                 clean_str = val_str.replace('_', '')
                 try:
                     parsed_int_val = int(clean_str, 2)
                 except ValueError:
                     parsed_int_val = 0

            # 通用數字/算式
            else:
                try:
                    parsed_int_val = int(float(val_str))
                except ValueError:
                    if re.match(r'^[0-9\+\-\*\/\(\)\.\s]+$', val_str):
                        try:
                            parsed_int_val = int(eval(val_str))
                        except:
                            parsed_int_val = 0
                    else:
                        parsed_int_val = 0
            
            # Bit Packing (數值轉二進制)
            if parsed_int_val < 0:
                parsed_int_val = (1 << signal['bits']) + parsed_int_val
            
            bin_segment = f"{parsed_int_val:0{signal['bits']}b}"
            
            if len(bin_segment) > signal['bits']:
                bin_segment = bin_segment[-signal['bits']:]
            
            instruction_bin_str += bin_segment

        # --- [修改 1] 填滿 144 bit，沒填滿就用 0 (補在後面) ---
        target_length = 144
        current_length = len(instruction_bin_str)
        
        if current_length < target_length:
            # 使用 ljust 在右側補 0 (例如: "101" -> "10100...")
            instruction_bin_str = instruction_bin_str.ljust(target_length, '0')
        elif current_length > target_length:
            # (選用) 如果超過 144 bit，您可能希望顯示警告，這裡目前保持原樣或截斷
            print(f"警告: 第 {base_row} 列產生的指令長度 ({current_length}) 超過 144 bits")
            # 若要強制截斷請取消下一行註解
            # instruction_bin_str = instruction_bin_str[:target_length]

        # --- 輸出處理 (僅保留二進制) ---
        if instruction_bin_str:
            bin_outputs.append(instruction_bin_str)

    # 確保輸出目錄存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 寫入 Bin 檔案
    with open(output_path, 'w') as f:
        for line in bin_outputs:
            f.write(line + '\n')
            
    print(f"Bin 檔案已寫入: {output_path}")
            
    return bin_outputs

# --- 執行設定 ---
# 請根據需要取消註解並修改路徑

input_excel = r'VLIW_Excel/Unit6_to_12_ShuffleUnit.xlsx'
output_txt = r'VLIW_txt/Unit6_to_12_ShuffleUnit.txt'




# 執行
result = parse_isa_to_bin(input_excel, output_txt)

if isinstance(result, list):
    print(f"轉換成功！已生成 {len(result)} 條指令。")
    if len(result) > 0:
        print(f"指令位元寬度 (Bits): {len(result[0])}") # 顯示總 Bit 數
else:
    print(result)