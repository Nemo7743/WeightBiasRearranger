import os

def package_tile_OGshuffle(layer_num):
    """
    修改後的 ShuffleNet (OG Shuffle) 打包邏輯：
    1. Filter: 輸出 24 個 Group，維持 Column-based (0, 24, 48...)。
    2. Bias:   輸出 6 個 Group，修改為 Row-based (0, 1, 2, 3, 24, 25...)。
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
    # [修改點 1] 不再建立子資料夾，統一輸出到根目錄
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
    print(f"偵測到 {total_files} 個 Filter，開始打包...")

    # ==========================================
    # --- 5. 處理 Filter (24 Groups) - [維持 Column Base] ---
    # ==========================================
    print("--- 正在處理 Filter (24 Groups) ---")
    
    for slot_idx in range(24):
        # 計算 Group 名稱
        major_group = slot_idx // 4  # 0~5
        minor_group = slot_idx % 4   # 0~3
        output_filename = f"Group{major_group}.{minor_group}.txt"

        # [邏輯不變] 找出屬於這個 Slot 的所有 Filter Index (間隔 24)
        target_indices = [idx for idx in filter_indices if idx % 24 == slot_idx]
        
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

        # [修改點 2] 合併寫入同一個檔案 (PW1 -> DW -> PW2)
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
    # --- 6. 處理 Bias (6 Major Groups) - [修改為 Row Base] ---
    # ==========================================
    print("\n--- 正在處理 Bias (6 Major Groups - Row Base) ---")
    
    # 計算最大深度 (例如 total=76, 76/24 = 3...4 -> max_depth = 4)
    max_depth = (total_files + 23) // 24

    for major_group in range(6):
        output_filename = f"Bias{major_group}.txt"
        
        content_pw1 = []
        content_dw  = []
        content_pw2 = []
        collected_indices = []

        # 該 Major Group 包含的基礎 Slot (例如 Group 0 -> [0, 1, 2, 3])
        base_slots = [major_group * 4 + i for i in range(4)]

        # [核心修改]: 實現 Row Base 順序
        # 1. 外層 Loop: Depth (對應偏移量 0, 24, 48...)
        # 2. 內層 Loop: Slot (0, 1, 2, 3)
        # 結果: 先拿第一層的 0,1,2,3，再拿第二層的 24,25,26,27...
        
        for depth in range(max_depth):
            offset = depth * 24
            for slot_idx in base_slots:
                target_idx = offset + slot_idx
                
                # 確認此 index 是否存在於原始檔案清單中 (避免讀取不存在的檔案)
                if target_idx in filter_indices_set:
                    collected_indices.append(target_idx)
                    
                    fname = f"Bias{target_idx}.txt" # 注意是讀取 Bias
                    
                    p_pw1 = os.path.join(src_pw1, fname)
                    p_dw  = os.path.join(src_dw, fname)
                    p_pw2 = os.path.join(src_pw2, fname)
                    
                    try:
                        with open(p_pw1, 'r', encoding='utf-8') as f: content_pw1.append(f.read().strip())
                        with open(p_dw,  'r', encoding='utf-8') as f: content_dw.append(f.read().strip())
                        with open(p_pw2, 'r', encoding='utf-8') as f: content_pw2.append(f.read().strip())
                    except FileNotFoundError:
                        # Bias 檔案允許部分遺失
                        pass

        # 合併寫入同一個檔案
        if content_pw1:
            text_pw1 = "\n".join(content_pw1)
            text_dw  = "\n".join(content_dw)
            text_pw2 = "\n".join(content_pw2)
            
            with open(os.path.join(base_output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(text_pw1)
                f.write("\n\n\n") 
                f.write(text_dw)
                f.write("\n\n\n")
                f.write(text_pw2)
                f.write("\n")
            
            # 顯示驗證 (若太長則縮略)
            display_indices = collected_indices[:16]
            indices_str = ", ".join(map(str, display_indices))
            if len(collected_indices) > 16:
                indices_str += " ..."
            print(f"  已生成 {output_filename} \t包含 Bias: [{indices_str}]")

    print("全部打包完成。")

# --- 測試執行區塊 ---
if __name__ == "__main__":
    # 測試執行 Layer 1
    layers_to_test = [14] # 你可以改為 range(0, 16) 測試全部
    
    for layer in layers_to_test:
        try:
            if layer in [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]:
                print(f"--- Processing Layer {layer} ---")
                package_tile_OGshuffle(layer)
                print("-" * 30)
        except Exception as e:
            print(f"Layer {layer} 執行失敗: {e}")