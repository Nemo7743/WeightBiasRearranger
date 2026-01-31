import os

def package_tile_downSampling_L(layer_num: int):
    """
    修改後的 DownSampling 打包邏輯：
    1. Filter: 修改為 Block Base 打包 (每 4 個 Group 一組依序填滿，內部間隔為 4)
    2. Bias:   修改為 Block Base 打包 (邏輯同上)，共 24 包
    """
    
    # --- 1. 參數驗證 ---
    valid_layers = {0, 4, 12}
    if layer_num not in valid_layers:
        raise ValueError(f"無效的 layer_num：{layer_num}。允許的值為：{valid_layers}")

    # --- 2. 路徑設定 ---
    tile_map = {
        0: "tile1.1",
        4: "tile5.1",
        12: "tile13.1"
    }
    mapped_tile_name = tile_map[layer_num]

    # 原始來源資料夾
    dw_folder_name = f"features.{layer_num}.banch1.0"
    pw_folder_name = f"features.{layer_num}.banch1.2"

    dw_source_dir = os.path.join("output_data_split", "dw_column_filters", dw_folder_name)
    pw_source_dir = os.path.join("output_data_split", "pw_column_filters", pw_folder_name)
    
    # 輸出根目錄
    base_output_dir = os.path.join("output_data_packaged", f"{mapped_tile_name}_DownSamplingL")
    
    # 建立輸出目錄
    output_dir = base_output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"已確認輸出目錄：\n  Main -> {output_dir}")

    # --- 3. 讀取並排序來源檔案 ---
    try:
        all_files = [f for f in os.listdir(dw_source_dir) if f.startswith("Filter") and f.endswith(".txt")]
    except FileNotFoundError:
        print(f"錯誤：找不到來源目錄 {dw_source_dir}")
        return

    # 依據數字大小排序
    all_files.sort(key=lambda x: int(x.replace("Filter", "").replace(".txt", "")))
    total_files = len(all_files)
    
    # 設定總輸出包數 (依據您的邏輯 weight0.0 ~ weight5.3 共 24 包)
    TOTAL_GROUPS = 24
    
    # 計算每包應該分配到幾個 Filter (例如 96/24 = 4, 48/24 = 2)
    if total_files % TOTAL_GROUPS != 0:
        print(f"[警告] 檔案總數 {total_files} 無法被 {TOTAL_GROUPS} 整除，可能會導致分配不均！")
    
    items_per_group = total_files // TOTAL_GROUPS
    
    print(f"偵測到 {total_files} 個 Filter，共 {TOTAL_GROUPS} 個 Group，每組分配 {items_per_group} 個檔案。")

    # ==========================================
    # --- 4. Filter 打包邏輯 (修改為 Block Base) ---
    # ==========================================
    print("--- Processing Filters (Block Base) ---")
    
    for slot_idx in range(TOTAL_GROUPS):
        major_group = slot_idx // 4  # 0~5
        minor_group = slot_idx % 4   # 0~3
        output_filename = f"Weight{major_group}.{minor_group}.txt"

        # --- 計算 Target Indices (核心修改) ---
        # 邏輯：
        # 1. 每個 Major Group (Row) 負責的總量 = items_per_group * 4 (因為有 4 個 Col)
        # 2. 該 Row 的起始 Index = major_group * (該 Row 負責的總量)
        # 3. 加上 minor_group 偏移 (0, 1, 2, 3)
        # 4. 在該 Row 範圍內，每隔 4 取一個值
        
        row_capacity = items_per_group * 4
        start_base_index = (major_group * row_capacity) + minor_group
        
        target_indices = []
        for k in range(items_per_group):
            idx = start_base_index + (k * 4)
            if idx < total_files:
                target_indices.append(idx)

        # 讀取檔案內容
        dw_content_list = []
        pw_content_list = []
        
        for filter_idx in target_indices:
            filename = f"Filter{filter_idx}.txt"
            dw_path = os.path.join(dw_source_dir, filename)
            pw_path = os.path.join(pw_source_dir, filename)
            
            try:
                with open(dw_path, 'r', encoding='utf-8') as f:
                    dw_content_list.append(f.read().strip())
                with open(pw_path, 'r', encoding='utf-8') as f:
                    pw_content_list.append(f.read().strip())
            except FileNotFoundError:
                print(f"  [警告] Filter 檔案遺失：{filename}")

        # 寫入檔案
        if dw_content_list:
            final_dw_text = "\n\n".join(dw_content_list)
            final_pw_text = "\n\n".join(pw_content_list)
            
            with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(final_dw_text)
                f.write("\n\n\n")
                f.write(final_pw_text)
                f.write("\n")
            
            indices_str = ", ".join([str(i) for i in target_indices])
            print(f"  已生成 {output_filename} \t包含 Filter: [{indices_str}]")
    
    # ==========================================
    # --- 5. Bias 打包邏輯 (修改為 Block Base) ---
    # ==========================================
    print("\n--- Processing Biases (Block Base) ---")
    
    # Bias 邏輯與 Weight 完全相同
    for slot_idx in range(TOTAL_GROUPS):
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        
        output_filename = f"Bias{major_group}.{minor_group}.txt"

        # 使用與 Filter 相同的計算邏輯
        row_capacity = items_per_group * 4
        start_base_index = (major_group * row_capacity) + minor_group
        
        target_indices = []
        for k in range(items_per_group):
            idx = start_base_index + (k * 4)
            # 這裡假設 Bias 數量與 Filter 數量一致，若不一致需另外讀取 bias 檔案列表計算
            target_indices.append(idx) 
        
        dw_content_list = []
        pw_content_list = []
        
        for filter_idx in target_indices:
            filename = f"Bias{filter_idx}.txt"
            dw_path = os.path.join(dw_source_dir, filename)
            pw_path = os.path.join(pw_source_dir, filename)
            
            try:
                with open(dw_path, 'r', encoding='utf-8') as f:
                    dw_content_list.append(f.read().strip())
                with open(pw_path, 'r', encoding='utf-8') as f:
                    pw_content_list.append(f.read().strip())
            except FileNotFoundError:
                # 某些情況下 Bias 可能比 Filter 少，如果不重要可忽略
                # print(f"  [資訊] Bias 檔案遺失：{filename} (可能無此 Bias)")
                pass

        if dw_content_list:
            final_dw_text = "\n\n".join(dw_content_list)
            final_pw_text = "\n\n".join(pw_content_list)
            
            with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(final_dw_text)
                f.write("\n\n\n")
                f.write(final_pw_text)
                f.write("\n")
            
            indices_str = ", ".join([str(i) for i in target_indices])
            print(f"  已生成 {output_filename} \t包含 Bias: [{indices_str}]")

    print("打包完成。")

# --- 測試執行 ---
if __name__ == "__main__":
    try:
        # 請根據實際狀況修改測試參數
        package_tile_downSampling_L(12) 
    except Exception as e:
        print(f"執行中發生錯誤: {e}")