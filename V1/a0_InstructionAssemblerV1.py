import pandas as pd
import os
import sys


def InstructionAssembler(instruction_file = 'data_instructions/InstructionSet.csv', input_file = 'data_instructions/instruction_input.txt', output_file = 'data_instructions/instruction_output.txt'):
    # 檢查指令集檔案是否存在
    if not os.path.exists(instruction_file):
        print(f"錯誤: 找不到 {instruction_file}")
        return

    # 1. 讀取並處理 instruction_file
    try:
        df = pd.read_csv(instruction_file)
        
        # 處理 CSV 空白欄位：'function' 欄位如果是空的，就繼承上一行的值
        df['function'] = df['function'].ffill()
        
        # 清除字串前後可能存在的空白
        df['function'] = df['function'].str.strip()
        df['opcode (指令)'] = df['opcode (指令)'].str.strip()
        df['opcode (Hex)'] = df['opcode (Hex)'].str.strip()
        
        # 建立指令對照字典 (Map)
        # Key: "Category.Command"
        # Value: {"hex": "HEX_CODE", "count": int(預期參數數量)}
        instruction_map = {}
        
        for _, row in df.iterrows():
            func = row['function']
            sub_op = row['opcode (指令)']
            hex_val = row['opcode (Hex)']
            
            
            # 格式化 Hex
            if str(hex_val).lower().startswith('0x'):
                clean_hex = hex_val[2:].upper()
            else:
                clean_hex = str(hex_val).upper()

            # 計算該指令需要的參數數量
            arg_count = int(clean_hex[3])
            
            # 組合 Key
            key = f"{func}.{sub_op}"
            
            # 存入字典，包含 Hex 與 參數數量
            instruction_map[key] = {
                "hex": clean_hex,
                "count": arg_count
            }
            
    except Exception as e:
        print(f"讀取 CSV 時發生錯誤: {e}")
        return

    # 2. 讀取 input.txt 並進行轉譯與檢查
    output_lines = []
    has_error = False # 標記是否有錯誤發生
    
    if not os.path.exists(input_file):
        print(f"錯誤: 找不到 {input_file}")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            lines = f_in.readlines()
            
        print("--- 開始組譯與檢查 ---")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            # 跳過空行
            if not line:
                continue
                
            parts = line.split()
            command = parts[0]
            args = parts[1:]
            
            # 查詢指令集
            if command in instruction_map:
                instr_info = instruction_map[command]
                opcode_hex = instr_info["hex"]
                expected_count = instr_info["count"]
                
                #參數數量檢查
                if len(args) != int(expected_count):
                    print(f"[Error] Line {line_num}: 指令 '{command}' 預期 {expected_count} 個參數，但偵測到 {len(args)} 個 ({args})。")
                    has_error = True
                    # 發生錯誤時，該行不寫入 output，或者寫入錯誤標記視需求而定
                    # 這裡選擇不寫入 output，以免硬體執行錯誤指令
                    continue
                
                # 若檢查通過，組合結果
                if args:
                    result_line = f"{opcode_hex} {' '.join(args)}"
                else:
                    result_line = opcode_hex
                
                output_lines.append(result_line)
            
            else:
                print(f"[Warning] Line {line_num}: 未知的指令 '{command}'，已略過。")
                has_error = True

        # 3. 輸出到 output.txt
        if output_lines:
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write('\n'.join(output_lines))
            
            if has_error:
                print(f"\n組譯完成，但過程中發現錯誤 (詳見上方 Log)。\n正確的指令已儲存至 {output_file}。")
            else:
                print(f"\n組譯成功！沒有發現語法錯誤。\n結果已儲存至 {output_file}")
        else:
            print("\n未產生任何輸出內容 (可能是輸入檔為空或所有指令皆有誤)。")

    except Exception as e:
        print(f"處理檔案時發生錯誤: {e}")


if __name__ == "__main__":
    # 檔案名稱設定
    instruction_file = 'data_instructions/InstructionSet.csv'
    input_file = 'data_instructions/instruction_input.txt'
    output_file = 'data_instructions/instruction_output.txt'

    InstructionAssembler(instruction_file, input_file, output_file)