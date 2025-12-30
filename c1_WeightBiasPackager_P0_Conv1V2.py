import os

def package_P0_Conv1():
    """
    讀取 output_data_split/conv1_column_filters 中的 Filter0.txt 到 Filter23.txt。
    
    修改後的邏輯：
    1. 輸出路徑變更為 output_data_packaged/P0_Conv1
    2. 不進行檔案內容合併 (1對1 輸出)。
    3. 命名規則轉換：
       Filter0 - Filter3   -> Group0.0 - Group0.3
       Filter4 - Filter7   -> Group1.0 - Group1.3
       ...
       Filter20 - Filter23 -> Group5.0 - Group5.3
    """
    
    # 1. 設定路徑
    source_dir = os.path.join("output_data_split", "conv1_column_filters")
    # [修改點 1] 輸出資料夾名稱改為 output_data_packaged/P0_Conv1
    output_dir = os.path.join("output_data_packaged", "P0_Conv1")

    # 2. 如果輸出目錄不存在，則自動建立
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"已確認輸出目錄：{output_dir}")
    print("正在將 24 個 Filter 轉換為 GroupX.Y 格式 (共 24 包)...")

    # 3. 迴圈處理 (總共 24 個檔案)
    for i in range(24):
        input_filename = f"Filter{i}.txt"
        input_path = os.path.join(source_dir, input_filename)
        
        # [修改點 2] 計算 Group 編號
        # // 是整除運算 (例如 0~3 除以 4 都會是 0; 4~7 除以 4 都會是 1)
        major_group = i // 4  
        # % 是取餘數運算 (例如 0,1,2,3 -> 0,1,2,3; 4,5,6,7 -> 0,1,2,3)
        minor_group = i % 4   
        
        output_filename = f"Group{major_group}.{minor_group}.txt"
        output_path = os.path.join(output_dir, output_filename)

        try:
            # 讀取原始 Filter
            with open(input_path, 'r', encoding='utf-8') as f_in:
                # 使用 strip() 去除前後多餘空白或換行，保持資料乾淨
                content = f_in.read().strip()
            
            # [修改點 3] 直接寫入對應的 Group 檔案 (不需合併)
            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write(content)
                
            print(f"  [{input_filename}] -> 轉換為 -> [{output_filename}]")

        except FileNotFoundError:
            print(f"錯誤: 找不到檔案 {input_path}，請檢查路徑或檔案名稱。")

    # 4. 顯示完成訊息
    print("-" * 30)
    print(f"打包完成，共生成 24 個檔案於 {output_dir}")

# --- 執行 Function ---
if __name__ == "__main__":
    package_P0_Conv1()