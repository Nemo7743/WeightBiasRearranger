import os

def package_tile17_convlast():
    """
    修改後的 Conv Last 打包邏輯：
    1. 輸出總共 24 個 Group (Group0.0 - Group5.3)。
    2. 總 Filter 數視為 1032 (實體 1024 + 補零 8)。
    3. 採間隔採樣 (Step=24)，每包包含 43 個 Filter。
    """
    
    # --- 1. 路徑設定 ---
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, 'output_data_split', 'conv_last_filters')
    
    # [修改點 1] 輸出路徑包含 P0 子目錄
    output_dir = os.path.join(base_dir, 'output_data_packaged', 'tile17_ConvLast', 'P0')

    # 建立目錄
    os.makedirs(output_dir, exist_ok=True)
    print(f"已確認輸出目錄：{output_dir}")

    # --- 2. 參數設定 ---
    TOTAL_GROUPS = 24             # 輸出 24 包
    TOTAL_REAL_FILTERS = 1024     # 真實存在的檔案 0~1023
    TOTAL_VIRTUAL_SLOTS = 1032    # 為了湊齊 24 的倍數 (43 * 24 = 1032)
    FILES_PER_GROUP = 43          # 每包 43 個

    # --- 3. 準備全 0 的 Filter 樣板 ---
    # 嘗試讀取 Filter0 作為格式參考，若無則建立預設值
    ref_file = os.path.join(input_dir, 'Filter0.txt')
    zero_filter_content = ""
    
    if os.path.exists(ref_file):
        with open(ref_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 替換每一行為全 0 (保留原始行數結構)
            zero_lines = ["0000 0000 0000 0000" for _ in lines]
            zero_filter_content = "\n".join(zero_lines)
    else:
        # 預設 49 行
        zero_lines = ["0000 0000 0000 0000"] * 49
        zero_filter_content = "\n".join(zero_lines)

    print(f"正在將 {TOTAL_VIRTUAL_SLOTS} 個過濾器分散處理為 {TOTAL_GROUPS} 組 (每組 {FILES_PER_GROUP} 個)...")

    # --- 4. 核心迴圈 (24 Groups) ---
    # slot_idx 代表 0~23 的硬體位置
    
    for slot_idx in range(TOTAL_GROUPS):
        
        # 計算 Group 檔名 (GroupX.Y)
        major_group = slot_idx // 4  # 0~5
        minor_group = slot_idx % 4   # 0~3
        output_filename = f"Group{major_group}.{minor_group}.txt"
        
        # 產生該 Group 負責的所有 Index (間隔為 24)
        # 例如 slot 0 -> [0, 24, 48, ..., 1008]
        # 例如 slot 16 -> [16, 40, ..., 1024(補零)]
        group_indices = list(range(slot_idx, TOTAL_VIRTUAL_SLOTS, TOTAL_GROUPS))
        
        group_content_list = []

        # 讀取或補零
        for current_filter_num in group_indices:
            
            # [修改點 2] 判斷是否為真實存在的 Filter
            if current_filter_num < TOTAL_REAL_FILTERS:
                file_path = os.path.join(input_dir, f'Filter{current_filter_num}.txt')
                
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        group_content_list.append(f.read().strip())
                else:
                    # 異常情況：應該存在但找不到 -> 視為 0
                    print(f"  [警告] 找不到實體檔案 Filter{current_filter_num}，以全0取代。")
                    group_content_list.append(zero_filter_content)
            else:
                # [修改點 3] 超出 1023 的部分 (1024~1031) -> 自動補零
                group_content_list.append(zero_filter_content)

        # --- 5. 寫入檔案 ---
        
        # 用雙換行連接
        full_group_text = "\n\n".join(group_content_list)
        
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(full_group_text)
            
        # 顯示格式化資訊 (顯示前幾個和最後一個)
        first_few = ", ".join(map(str, group_indices[:2])) 
        last_one = group_indices[-1]
        
        # 標註最後一個是否為虛擬補零
        note = "(含補零)" if last_one >= TOTAL_REAL_FILTERS else ""
        
        print(f"  已生成 {output_filename:<15} 包含: [{first_few}, ..., {last_one}] {note}")

    print("打包完成。")

if __name__ == "__main__":
    package_tile17_convlast()