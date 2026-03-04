import os

def convert_to_coe(input_filename):
    # 檢查檔案是否存在
    if not os.path.exists(input_filename):
        print(f"Error: 找不到檔案 '{input_filename}'")
        return

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 將文字檔中所有的換行修改為逗號","
        # 注意：有些檔案可能由 Windows 產生 (\r\n)，有些是 Linux (\n)
        # 統一將 \n 換成 , (Python 的 text mode 會自動處理 \r\n 為 \n，所以 replace \n 即可)
        processed_content = content.replace('\n', ',')

        # 處理標頭
        header = "memory_initialization_radix=16;\nmemory_initialization_vector=\n"
        
        # 3. 檢查文字檔最後一個字元
        if processed_content:
            last_char = processed_content[-1]
            if last_char.isalnum():
                # 如果是英數字，就直接在後面加上分號";"
                final_content = processed_content + ";"
            else:
                # 如果不英數字，就刪除並替換為分號";"
                # 例如最後是逗號的情况
                final_content = processed_content[:-1] + ";"
        else:
            final_content = ";" # 空檔案處理

        # 組合最終內容
        output_content = header + final_content

        # 產生輸出檔名 (將 .txt 換成 .coe)
        output_filename = os.path.splitext(input_filename)[0] + ".coe"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(output_content)

        print(f"成功將 '{input_filename}' 轉換為 '{output_filename}'")

    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    # 設定要轉換的檔案名稱 (直接在此修改)
    TARGET_FILENAME = "Unit1_1_DownSamplingL.txt"

    if TARGET_FILENAME:
        convert_to_coe(TARGET_FILENAME)
        
    input("按 Enter 鍵結束...")