def split_fixed_length_string(input_file, output_file):
    # 定義你要求的切割長度清單
    lengths = [6, 5, 3, 4, 12, 8, 7, 8, 7, 8, 3, 3, 3, 3, 3, 3, 2, 14, 8, 14, 8, 12]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            
            for line in f_in:
                # 去除行尾換行符號與前後空格
                data = line.strip()
                
                if not data:
                    continue
                
                # 檢查長度是否符合 144 bit (可選)
                if len(data) != 144:
                    print(f"警告：發現長度不為 144 的行 (長度: {len(data)})，已跳過或照常處理。")
                
                # 根據 lengths 進行切割
                parts = []
                start = 0
                for length in lengths:
                    parts.append(data[start : start + length])
                    start += length
                
                # 用空格連接各個部分並寫入新檔案
                processed_line = " ".join(parts)
                f_out.write(processed_line + "\n")
                
        print(f"處理完成！結果已儲存至: {output_file}")

    except FileNotFoundError:
        print("錯誤：找不到輸入檔案，請檢查路徑。")

# --- 執行部分 ---
# 請將 'input.txt' 換成你原始檔案的名稱
# 'output.txt' 則是輸出後的檔案名稱
split_fixed_length_string('Unit17_ConvLast_ClobalAveragePool_FC.txt', 'testing_cutting/output.txt')