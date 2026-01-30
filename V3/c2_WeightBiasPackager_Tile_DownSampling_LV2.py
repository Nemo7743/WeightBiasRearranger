import os

def package_tile_downSampling_L(layer_num: int):
    """
    修改後的 DownSampling 打包邏輯：
    1. Filter: 維持 Column base 打包 (Group0.0 包含 0, 24, 48...)
    2. Bias:   修改為 Row base 打包 (Bias0 包含 0, 1, 2, 3, 24, 25, 26, 27...)
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
    
    # 建立 P0_DW 和 P1_PW 子目錄 (雖然寫入邏輯目前是合併，但保留目錄結構)
    dw_output_dir = os.path.join(base_output_dir, "P0_DW")
    pw_output_dir = os.path.join(base_output_dir, "P1_PW")
    output_dir = base_output_dir

    os.makedirs(dw_output_dir, exist_ok=True)
    os.makedirs(pw_output_dir, exist_ok=True)
    
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
    
    print(f"偵測到 {total_files} 個 Filter，開始打包...")

    # ==========================================
    # --- 4. Filter 打包邏輯 (維持不變) ---
    # ==========================================
    print("--- Processing Filters (Column Base) ---")
    for slot_idx in range(24):
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Group{major_group}.{minor_group}.txt"

        target_indices = list(range(slot_idx, total_files, 24))
        
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
    # --- 5. Bias 打包邏輯 (修改為 Row Base) ---
    # ==========================================
    print("\n--- Processing Biases (Row Base) ---")
    
    # [修改邏輯]: Bias 共有 6 個 Major Group (Bias0 - Bias5)
    # 每個 Major Group 對應 4 個連續的 Slot (例如 Group 0 對應 Slot 0,1,2,3)
    # 我們需要先遍歷這些 Slot (Row)，再往下疊加 24 (Depth)
    
    major_group_count = 6  # 24 slots / 4 = 6 groups
    
    for major_idx in range(major_group_count):
        output_filename = f"Bias{major_idx}.txt"
        
        # 該 Major Group 包含的基礎 Slot (例如 Group 0 -> [0, 1, 2, 3])
        base_slots = [major_idx * 4 + i for i in range(4)]
        
        # 計算需要堆疊幾層 (Depth)
        # 例如 total=76, 76/24 = 3...4 -> 需要跑 4 層 (0, 1, 2, 3)
        max_depth = (total_files + 23) // 24 
        
        target_indices = []
        
        # [關鍵修改]: 巢狀迴圈順序決定了 Row Base
        # 外層 loop Depth (0, 24, 48...)
        # 內層 loop Slot (0, 1, 2, 3)
        for depth in range(max_depth):
            offset = depth * 24
            for slot in base_slots:
                target_idx = slot + offset
                # 確保不超出總檔案數
                if target_idx < total_files:
                    target_indices.append(target_idx)
        
        # --- 讀取檔案與寫入 ---
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
                print(f"  [警告] Bias 檔案遺失：{filename} (跳過)")

        if dw_content_list:
            final_dw_text = "\n".join(dw_content_list)
            final_pw_text = "\n".join(pw_content_list)
            
            with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(final_dw_text)
                f.write("\n\n\n")
                f.write(final_pw_text)
                f.write("\n")
            
            # 顯示進度 (方便驗證順序)
            # 如果 indices 太多，只顯示前 16 個以供檢查
            display_indices = target_indices[:16]
            indices_str = ", ".join([str(i) for i in display_indices])
            if len(target_indices) > 16:
                indices_str += " ..."
            print(f"  已生成 {output_filename} \t包含 Bias: [{indices_str}]")

    print("打包完成。")

# --- 測試執行 ---
if __name__ == "__main__":
    try:
        # 請根據實際狀況修改測試參數
        package_tile_downSampling_L(12) 
    except Exception as e:
        print(f"執行中發生錯誤: {e}")