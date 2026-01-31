import os

def package_tile_downSampling_L(layer_num: int):
    """
    修改後的 DownSampling 打包邏輯：
    1. Filter: 維持 Column base 打包 (Group0.0 包含 0, 24, 48...)
    2. Bias:   已修改為 Column base 打包 (Bias0.0 包含 0, 24, 48...)，共 24 包
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
    
    # 建立 P0_DW 和 P1_PW 子目錄
    output_dir = base_output_dir
    
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
        output_filename = f"Weight{major_group}.{minor_group}.txt"

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
    # --- 5. Bias 打包邏輯 (修改為 Column Base) ---
    # ==========================================
    print("\n--- Processing Biases (Column Base) ---")
    
    # [修改邏輯]: 現在 Bias 邏輯與 Weight 完全相同，共 24 個 Group
    for slot_idx in range(24):
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        
        # 檔名改為 BiasX.Y.txt
        output_filename = f"Bias{major_group}.{minor_group}.txt"

        # 使用與 Filter 相同的 Column Base 邏輯 (跳號選取: 0, 24, 48...)
        target_indices = list(range(slot_idx, total_files, 24))
        
        dw_content_list = []
        pw_content_list = []
        
        for filter_idx in target_indices:
            filename = f"Bias{filter_idx}.txt"  # 讀取 Bias 檔案
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
            # 這裡維持與 bias 原始邏輯一致，通常 bias 之間用單個 \n 或與 weight 一樣用 \n\n 
            # 既然要求與 Weight 邏輯相同，這裡採用與 Weight 相同的拼接方式 (\n\n)
            # 若原 Bias 只需要 \n，可將下方的 "\n\n" 改為 "\n"
            final_dw_text = "\n\n".join(dw_content_list)
            final_pw_text = "\n\n".join(pw_content_list)
            
            with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(final_dw_text)
                f.write("\n\n\n")
                f.write(final_pw_text)
                f.write("\n")
            
            # 格式化輸出訊息
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