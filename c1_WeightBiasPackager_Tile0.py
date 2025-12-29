import os

def package_tile0():
    """
    讀取 output_data_split/conv1_column_filters 中的 Filter0.txt 到 Filter23.txt。
    每 4 個 Filter 為一組 (0-3, 4-7, ...)，合併內容並以換行隔開。
    輸出至 output_data_packaged/tile0 資料夾。
    """
    
    # 1. 設定相對路徑
    source_dir = os.path.join("output_data_split", "conv1_column_filters")
    output_dir = os.path.join("output_data_packaged", "tile0")

    # 2. 如果輸出目錄不存在，則自動建立
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已建立目錄: {output_dir}")

    # 3. 迴圈處理分組
    # range(0, 24, 4) 會產生: 0, 4, 8, 12, 16, 20
    for start_idx in range(0, 24, 4):
        group_contents = []
        end_idx = start_idx + 3
        
        # 讀取該組內的 4 個檔案
        for offset in range(4):
            current_filter_idx = start_idx + offset
            input_filename = f"Filter{current_filter_idx}.txt"
            input_path = os.path.join(source_dir, input_filename)
            
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    # 讀取內容，並使用 strip() 去除原始檔案末尾可能多餘的換行，確保合併時格式乾淨
                    content = f.read().strip()
                    group_contents.append(content)
            except FileNotFoundError:
                print(f"錯誤: 找不到檔案 {input_path}，請檢查路徑或檔案名稱。")
                return

        # 4. 將 4 個檔案的內容以換行符號 (\n) 連接
        combined_text = "\n\n".join(group_contents)

        # 5. 寫入輸出檔案
        # 檔名範例: Group_0-3.txt (你可以根據喜好修改命名格式)
        output_filename = f"Group{start_idx//4}.txt"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(combined_text)

        print(f"完成輸出: {output_path}")

# --- 執行 Function ---
if __name__ == "__main__":
    # 請確保你的 Python 腳本是放在專案的「根目錄」下執行
    package_tile0()