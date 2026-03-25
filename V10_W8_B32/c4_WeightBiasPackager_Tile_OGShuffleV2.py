import os

def package_tile_OGshuffle(layer_num):
    """
    修改後的 ShuffleNet (OG Shuffle) 打包邏輯：
    1. Filter: 輸出 24 個 Group。
       邏輯變更：平均分配總數後，採 Block Base 方式 (每 4 個 Group 一組填滿後再填下一組)。
    2. Bias:   已修改為與 Filter 相同，輸出 24 個 Group (Bias0.0 - Bias5.3)，邏輯同上。
    3. 合併儲存: 每個檔案內依序包含 PW1 -> DW -> PW2 的內容，不分資料夾。
    
    參數:
        layer_num (int): 層級識別碼。
    """
    
    # --- 1. 驗證與路徑映射 ---
    valid_layers = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]
    if layer_num not in valid_layers:
        raise ValueError(f"無效的 layer_num。預期為 {valid_layers}。")

    # Tile 名稱映射
    tile_map = {
        1: "tile2.2", 2: "tile3.2", 3: "tile4.2", 
        5: "tile6.2", 6: "tile7.2", 7: "tile8.2", 8: "tile9.2",
        9: "tile10.2", 10: "tile11.2", 11: "tile12.2", 
        13: "tile14.2", 14: "tile15.2", 15: "tile16.2"
    }
    tile_name = tile_map[layer_num]

    # --- 2. 設定來源路徑 ---
    base_split = "output_data_split"
    # OG Shuffle (Right Branch) 的三個來源
    src_pw1 = os.path.join(base_split, "pw_column_filters", f"features.{layer_num}.banch2.0")
    src_dw  = os.path.join(base_split, "dw_column_filters", f"features.{layer_num}.banch2.3")
    src_pw2 = os.path.join(base_split, "pw_column_filters", f"features.{layer_num}.banch2.5")

    # --- 3. 設定輸出路徑結構 ---
    # 不再建立子資料夾，統一輸出到根目錄
    base_output_dir = os.path.join("output_data_packaged", f"{tile_name}_OGShuffle")
    os.makedirs(base_output_dir, exist_ok=True)

    print(f"已確認輸出目錄：{base_output_dir}")

    # --- 4. 取得並排序 Filter 索引 ---
    try:
        # 掃描 PW1 目錄
        all_files = [f for f in os.listdir(src_pw1) if f.startswith("Filter") and f.endswith(".txt")]
    except FileNotFoundError:
        print(f"錯誤：找不到來源目錄 {src_pw1}")
        return

    # 提取數字並排序
    filter_indices = []
    for f in all_files:
        try:
            # 取出 'Filter' 與 '.txt' 中間的數字
            idx = int(f.replace("Filter", "").replace(".txt", ""))
            filter_indices.append(idx)
        except ValueError:
            continue
    filter_indices.sort()
    
    # 建立 Set 加速查找 (Bias 用)
    filter_indices_set = set(filter_indices)
    
    total_files = len(filter_indices)
    
    # [新增] 計算分組參數
    TOTAL_GROUPS = 24
    if total_files > 0:
        items_per_group = total_files // TOTAL_GROUPS
    else:
        items_per_group = 0

    print(f"偵測到 {total_files} 個 Filter，共 24 組，每組分配 {items_per_group} 個檔案，開始打包...")

    # ==========================================
    # --- 5. 處理 Filter (24 Groups) - [修改為 Block Base] ---
    # ==========================================
    print("--- 正在處理 Filter (24 Groups) ---")
    
    for slot_idx in range(TOTAL_GROUPS):
        # 計算 Group 名稱
        major_group = slot_idx // 4  # 0~5 (Row)
        minor_group = slot_idx % 4   # 0~3 (Column)
        output_filename = f"Weight{major_group}.{minor_group}.txt"

        # [修改邏輯] 計算目標索引 (Block Base + Local Stride 4)
        # 1. 每個 Row (Major Group) 負責處理的數量 = items_per_group * 4
        # 2. 該 Row 的起始位置 (base_index_pos) = major_group * row_capacity
        # 3. 加上 minor_group 偏移，並在區塊內以 4 為間隔取值
        
        row_capacity = items_per_group * 4
        base_index_pos = (major_group * row_capacity) + minor_group
        
        target_indices = []
        for k in range(items_per_group):
            # 計算在 filter_indices 列表中的位置
            list_pos = base_index_pos + (k * 4)
            
            # 確保不超出範圍
            if list_pos < total_files:
                target_indices.append(filter_indices[list_pos])
        
        # 準備容器
        content_pw1 = []
        content_dw  = []
        content_pw2 = []

        for idx in target_indices:
            fname = f"Filter{idx}.txt"
            
            p_pw1 = os.path.join(src_pw1, fname)
            p_dw  = os.path.join(src_dw, fname)
            p_pw2 = os.path.join(src_pw2, fname)
            
            try:
                # 讀取三個檔案
                with open(p_pw1, 'r', encoding='utf-8') as f: content_pw1.append(f.read().strip())
                with open(p_dw,  'r', encoding='utf-8') as f: content_dw.append(f.read().strip())
                with open(p_pw2, 'r', encoding='utf-8') as f: content_pw2.append(f.read().strip())
            except FileNotFoundError:
                print(f"  [警告] Filter{idx} 的部分檔案遺失，跳過。")

        # 合併寫入同一個檔案 (PW1 -> DW -> PW2)
        if content_pw1:
            text_pw1 = "\n\n".join(content_pw1)
            text_dw  = "\n\n".join(content_dw)
            text_pw2 = "\n\n".join(content_pw2)

            with open(os.path.join(base_output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(text_pw1)
                f.write("\n\n\n")  # 分隔線
                f.write(text_dw)
                f.write("\n\n\n")  # 分隔線
                f.write(text_pw2)
                f.write("\n")
            
            # 顯示進度
            indices_str = ", ".join(map(str, target_indices))
            print(f"  已生成 {output_filename} \t包含 Filter: [{indices_str}]")

    # ==========================================
    # --- 6. 處理 Bias (24 Groups) - [修改為 Block Base] ---
    # ==========================================
    print("\n--- 正在處理 Bias (24 Groups - Column Base) ---")
    
    # [修改邏輯]: Bias 使用與 Filter 完全相同的 24 Group 邏輯
    for slot_idx in range(TOTAL_GROUPS):
        # 計算 Group 名稱 (BiasX.Y)
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Bias{major_group}.{minor_group}.txt"

        # [修改邏輯]: 重複使用 Filter 的索引計算方式
        row_capacity = items_per_group * 4
        base_index_pos = (major_group * row_capacity) + minor_group
        
        target_indices = []
        for k in range(items_per_group):
            list_pos = base_index_pos + (k * 4)
            if list_pos < total_files:
                target_indices.append(filter_indices[list_pos])
        
        content_pw1 = []
        content_dw  = []
        content_pw2 = []
        collected_indices = []

        for idx in target_indices:
            fname = f"Bias{idx}.txt" # 讀取 Bias 檔名
            
            p_pw1 = os.path.join(src_pw1, fname)
            p_dw  = os.path.join(src_dw, fname)
            p_pw2 = os.path.join(src_pw2, fname)
            
            try:
                # 讀取三個檔案
                with open(p_pw1, 'r', encoding='utf-8') as f: content_pw1.append(f.read().strip())
                with open(p_dw,  'r', encoding='utf-8') as f: content_dw.append(f.read().strip())
                with open(p_pw2, 'r', encoding='utf-8') as f: content_pw2.append(f.read().strip())
                collected_indices.append(idx)
            except FileNotFoundError:
                # Bias 檔案允許部分遺失
                pass

        # 合併寫入同一個檔案
        if content_pw1:
            # 這裡為了與 Filter 邏輯保持一致，使用相同的拼接符
            text_pw1 = "\n\n".join(content_pw1)
            text_dw  = "\n\n".join(content_dw)
            text_pw2 = "\n\n".join(content_pw2)
            
            with open(os.path.join(base_output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(text_pw1)
                f.write("\n\n\n") 
                f.write(text_dw)
                f.write("\n\n\n")
                f.write(text_pw2)
                f.write("\n")
            
            # 顯示驗證
            indices_str = ", ".join(map(str, collected_indices))
            print(f"  已生成 {output_filename} \t包含 Bias: [{indices_str}]")

    print("全部打包完成。")

# --- 測試執行區塊 ---
if __name__ == "__main__":
    # 測試執行 Layer 14
    layers_to_test = [14] 
    
    for layer in layers_to_test:
        try:
            if layer in [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]:
                print(f"--- Processing Layer {layer} ---")
                package_tile_OGshuffle(layer)
                print("-" * 30)
        except Exception as e:
            print(f"Layer {layer} 執行失敗: {e}")