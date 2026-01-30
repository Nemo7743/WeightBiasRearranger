import os

def package_tile17_convlast():
    """
    修改後的 Conv Last 打包邏輯：
    1. Filter: 輸出 24 個 Group，採 Column-based (0, 24, 48...)。
    2. Bias:   已修改為與 Filter 相同，輸出 24 個 Group，採 Column-based (0, 24, 48...)。
    3. 補零:   總數視為 1032 (實體 1024 + 補零 8)。Bias 也需補零。
    """
    
    # --- 1. 路徑設定 ---
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, 'output_data_split', 'conv_last_filters')
    
    # 輸出路徑
    output_dir = os.path.join(base_dir, 'output_data_packaged', 'tile17_ConvLast')

    # 建立目錄
    os.makedirs(output_dir, exist_ok=True)
    print(f"已確認輸出目錄：{output_dir}")

    # --- 2. 參數設定 ---
    TOTAL_GROUPS = 24             # Filter 分 24 包
    TOTAL_REAL_FILTERS = 1024     # 真實存在的檔案 0~1023
    TOTAL_VIRTUAL_SLOTS = 1032    # 為了湊齊 24 的倍數 (43 * 24 = 1032)
    FILES_PER_GROUP = 43          # 每包 43 個 Filter (1032 / 24)

    # --- 3. 準備全 0 的樣板 (Filter 和 Bias 用) ---
    
    # [Filter 樣板]
    ref_file = os.path.join(input_dir, 'Filter0.txt')
    zero_filter_content = ""
    if os.path.exists(ref_file):
        with open(ref_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            zero_lines = ["0000 0000 0000 0000" for _ in lines] # 替換內容保留行數
            zero_filter_content = "\n".join(zero_lines)
    else:
        zero_filter_content = "\n".join(["0000 0000 0000 0000"] * 49) # 預設值

    # [Bias 樣板] (通常 Bias 只有一行或少量行數，這裡假設為全 0)
    # 嘗試讀取 Bias0 抓取格式，若無則預設 "00000000"
    ref_bias_file = os.path.join(input_dir, 'Bias0.txt')
    zero_bias_content = "00000000" # 預設值
    if os.path.exists(ref_bias_file):
         with open(ref_bias_file, 'r', encoding='utf-8') as f:
            # 讀取內容但不使用，僅作為存在確認，或者可以動態生成等長0
            # 這裡簡單假設使用標準8碼0
            zero_bias_content = "00000000"

    print(f"正在處理 {TOTAL_VIRTUAL_SLOTS} 個單元 (實體 {TOTAL_REAL_FILTERS} + 補零 8)...")

    # ==========================================
    # --- 4. Filter 打包 (Column Base) ---
    # ==========================================
    print("--- 正在處理 Filter (Column Base) ---")
    
    for slot_idx in range(TOTAL_GROUPS):
        
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Group{major_group}.{minor_group}.txt"
        
        # 產生該 Group 負責的所有 Index (間隔為 24)
        group_indices = list(range(slot_idx, TOTAL_VIRTUAL_SLOTS, TOTAL_GROUPS))
        
        group_content_list = []

        for current_filter_num in group_indices:
            
            if current_filter_num < TOTAL_REAL_FILTERS:
                file_path = os.path.join(input_dir, f'Filter{current_filter_num}.txt')
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        group_content_list.append(f.read().strip())
                else:
                    print(f"  [警告] 找不到實體檔案 Filter{current_filter_num}，以全0取代。")
                    group_content_list.append(zero_filter_content)
            else:
                # 補零區域
                group_content_list.append(zero_filter_content)

        # 寫入檔案
        full_group_text = "\n\n".join(group_content_list)
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(full_group_text)
            
        # 顯示資訊
        first_few = ", ".join(map(str, group_indices[:2]))
        last_one = group_indices[-1]
        note = "(含補零)" if last_one >= TOTAL_REAL_FILTERS else ""
        print(f"  已生成 {output_filename:<15} 包含 Filter: [{first_few}, ..., {last_one}] {note}")

    # ==========================================
    # --- 5. Bias 打包 (Column Base) ---
    # ==========================================
    print("\n--- 正在處理 Bias (Column Base) ---")
    
    # [修改邏輯]: Bias 改為與 Filter 完全相同的 24 Group (Column Base)
    # 也需要處理到 TOTAL_VIRTUAL_SLOTS (1032)
    
    for slot_idx in range(TOTAL_GROUPS):
        
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Bias{major_group}.{minor_group}.txt"
        
        # 產生該 Group 負責的所有 Index (間隔為 24，Column Base)
        group_indices = list(range(slot_idx, TOTAL_VIRTUAL_SLOTS, TOTAL_GROUPS))
        
        content_list = []
        collected_indices = [] # 用於顯示實際包含的 index (含補零)
        
        for current_bias_num in group_indices:
            
            collected_indices.append(current_bias_num)
            
            if current_bias_num < TOTAL_REAL_FILTERS:
                file_path = os.path.join(input_dir, f'Bias{current_bias_num}.txt')
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_list.append(f.read().strip())
                else:
                    # Bias 實體檔案遺失時補零
                    # print(f"  [警告] Bias{current_bias_num} 遺失，補零。") 
                    content_list.append(zero_bias_content)
            else:
                # 虛擬補零區 (Bias 1024 ~ 1031)
                content_list.append(zero_bias_content)

        # 寫入檔案 
        # 為了與 Filter 保持一致性，這裡使用 \n\n 分隔 (若 Bias 內容短且希望緊湊，可改 \n)
        if content_list:
            full_text = "\n\n".join(content_list)
            with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            # 顯示資訊
            first_few = ", ".join(map(str, collected_indices[:2]))
            last_idx = collected_indices[-1]
            note = "(含補零)" if last_idx >= TOTAL_REAL_FILTERS else ""
            
            print(f"  已生成 {output_filename:<15} 包含 Bias:   [{first_few}, ..., {last_idx}] {note}")

    print("打包完成。")

if __name__ == "__main__":
    package_tile17_convlast()