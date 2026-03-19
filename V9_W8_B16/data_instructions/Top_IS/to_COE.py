import pandas as pd
import numpy as np

def generate_coe(input_filename, output_filename='output.coe'):
    try:
        # 讀取 .xlsx 檔案使用 read_excel
        try:
            df = pd.read_excel(input_filename, engine='openpyxl')
        except ImportError:
            print("錯誤：缺少 'openpyxl' 套件。")
            print("請先執行指令安裝：pip install openpyxl")
            return
        except Exception as e:
            print(f"讀取 Excel 檔案時發生錯誤：{e}")
            return
        
        # 尋找關鍵欄位索引
        try:
            opcode_col_idx = df.columns.get_loc('Opcode')
            function_col_idx = df.columns.get_loc('function')
        except KeyError as e:
            print(f"錯誤：在檔案中找不到欄位 {e}。請確認 Excel 標題列名稱是否正確。")
            return

        coe_lines = []

        # 定義判斷空儲存格的函式
        def is_empty_cell(val):
            if pd.isna(val):
                return True
            s = str(val).strip().lower()
            return s == 'nan' or s == ''

        # 定義數值解析函式
        def parse_value(val, force_binary=False, row_idx=0):
            if is_empty_cell(val):
                return 0
            
            s = str(val).strip()
            
            if force_binary:
                try:
                    if '.' in s:
                        s = str(int(float(s)))
                    return int(s, 2)
                except ValueError:
                    print(f"警告 (Row {row_idx}): 無法將 '{s}' 強制轉換為二進制，將預設為 0")
                    return 0

            # 原有邏輯：自動判斷
            if len(s) > 1 and s.startswith('0') and all(c in '01' for c in s):
                try:
                    return int(s, 2)
                except:
                    pass
            try:
                return int(float(s))
            except ValueError:
                return 0

        # 【新增】定義高低位轉換邏輯函式
        def process_16bit_data(high_raw, low_raw, force_bin, row_idx, field_name):
            high_is_empty = is_empty_cell(high_raw)
            low_val = parse_value(low_raw, force_binary=force_bin, row_idx=row_idx)
            
            # 偵測低位是否超出 8-bit (即 > 255)
            if low_val > 255:
                if high_is_empty:
                    # 條件 a: 低位超出 8bit 且 高位為空 -> 直接把低位當作 16bit 寬度轉換
                    return low_val & 0xFFFF # 加上 & 0xFFFF 確保不會超過 16-bit 總寬度
                else:
                    # 條件 b: 低位超出 8bit 但 高位並非空儲存格 -> 報錯
                    raise ValueError(
                        f"資料錯誤 (Row {row_idx}): {field_name} 的低位數值 ({low_val}) 超出 8-bit 上限，"
                        f"但其高位儲存格包含數值 '{high_raw}'。請檢查 Excel 填寫是否正確！"
                    )
            else:
                # 正常情況：低位未超出 8-bit
                high_val = 0 if high_is_empty else parse_value(high_raw, force_binary=force_bin, row_idx=row_idx)
                # 嚴謹起見，高位和低位都加上 0xFF 遮罩再組合
                return ((high_val & 0xFF) << 8) | (low_val & 0xFF)

        # 遍歷每一行資料
        for index, row in df.iterrows():
            func_name = str(row.iloc[function_col_idx]).strip()
            is_force_binary = (func_name == "change buffer sel")

            # 1. 處理 Opcode (8 bits)
            raw_opcode = str(row.iloc[opcode_col_idx]).strip()
            
            if is_empty_cell(raw_opcode):
                opcode_val = 0
            else:
                try:
                    raw_opcode = str(int(float(raw_opcode))).zfill(3)
                except:
                    raw_opcode = raw_opcode.zfill(3)

                try:
                    d1, d2, d3 = int(raw_opcode[0]), int(raw_opcode[1]), int(raw_opcode[2])
                    opcode_val = (d1 * 32) + (d2 * 4) + d3
                except (ValueError, IndexError):
                    opcode_val = 0

            # 2. 處理 Num1 (16 bits) - 套用高低位轉換邏輯 (假設 Opcode 在 idx, Num1 高低位分別在 idx+1, idx+2)
            try:
                num1_val = process_16bit_data(
                    high_raw=row.iloc[opcode_col_idx + 1], 
                    low_raw=row.iloc[opcode_col_idx + 2], 
                    force_bin=is_force_binary, 
                    row_idx=index, 
                    field_name="Num1"
                )
            except ValueError as ve:
                print(f"【轉換中斷】{ve}")
                return # 遇到嚴重的資料矛盾，停止轉換

            # 3. 處理 Num2 (16 bits) - 套用高低位轉換邏輯 (假設 Num2 高低位分別在 idx+3, idx+4)
            try:
                num2_val = process_16bit_data(
                    high_raw=row.iloc[opcode_col_idx + 3], 
                    low_raw=row.iloc[opcode_col_idx + 4], 
                    force_bin=is_force_binary, 
                    row_idx=index, 
                    field_name="Num2"
                )
            except ValueError as ve:
                print(f"【轉換中斷】{ve}")
                return

            # 4. 格式化為二進制字串 (確保總寬度為 8 + 16 + 16 = 40 bits)
            binary_line = f"{opcode_val:08b}{num1_val:016b}{num2_val:016b}"
            coe_lines.append(binary_line)

        # 5. 填充至 256 條地址
        target_depth = 256
        if len(coe_lines) > target_depth:
            coe_lines = coe_lines[:target_depth]
        else:
            zero_padding = "0" * 40
            while len(coe_lines) < target_depth:
                coe_lines.append(zero_padding)

        # 6. 寫入 .coe 檔案
        with open(output_filename, 'w') as f:
            f.write("memory_initialization_radix=2;\n")
            f.write("memory_initialization_vector=\n")
            for line in coe_lines:
                f.write(line + "\n")

        print(f"轉換完成！已輸出至 {output_filename}")
        print(f"共產生 {len(coe_lines)} 條指令。")

    except Exception as e:
        print(f"發生未預期的錯誤: {e}")

# 執行轉換
#input_file = 'IS_260228.xlsx'
#output = "IS_All.coe"

input_file = 'IS_260301.xlsx'
output = "IS.coe"
generate_coe(input_file, output)