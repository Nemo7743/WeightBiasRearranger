import os

def package_tile0():
    """
    讀取 output_data_split/conv1_column_filters 中的 Filter0.txt 到 Filter23.txt。
    
    修改後的邏輯：
    共輸出 6 個 Group (Group0 - Group5)。
    每個 Group 包含 4 個 Filter，間隔為 6。
    例如 Group 0: 0, 6, 12, 18
         Group 1: 1, 7, 13, 19
    """
    
    # 1. 設定相對路徑
    source_dir = os.path.join("output_data_split", "conv1_column_filters")
    output_dir = os.path.join("output_data_packaged", "tile0")

    # 2. 如果輸出目錄不存在，則自動建立
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已建立目錄: {output_dir}")

    # 3. 迴圈處理分組
    # 總共要產生 6 包 (Group0 到 Group5)
    for group_idx in range(6):
        group_contents = []
        
        # 每一包裡面要有 4 個 Filter (總共 24 / 6 = 4)
        # 邏輯：基底是 group_idx，每次跳 6 號
        # 例如 group_idx=0 -> 0, 6, 12, 18
        # 例如 group_idx=1 -> 1, 7, 13, 19
        for step in range(4):
            current_filter_idx = group_idx + (step * 6)
            
            input_filename = f"Filter{current_filter_idx}.txt"
            input_path = os.path.join(source_dir, input_filename)
            
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    # 讀取內容，並使用 strip() 去除原始檔案末尾可能多餘的換行
                    content = f.read().strip()
                    group_contents.append(content)
            except FileNotFoundError:
                print(f"錯誤: 找不到檔案 {input_path}，請檢查路徑或檔案名稱。")
                return

        # 4. 將 4 個檔案的內容以換行符號 (\n\n) 連接
        # 註：這裡保留原本的 \n\n，如果你希望緊湊一點可以改成 \n
        combined_text = "\n\n".join(group_contents)

        # 5. 寫入輸出檔案
        # 檔名直接使用 group_idx 命名，例如 Group0.txt
        output_filename = f"Group{group_idx}.txt"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(combined_text)

        print(f"完成輸出: {output_path} (包含 Filters: {[group_idx + i*6 for i in range(4)]})")

# --- 執行 Function ---
if __name__ == "__main__":
    package_tile0()