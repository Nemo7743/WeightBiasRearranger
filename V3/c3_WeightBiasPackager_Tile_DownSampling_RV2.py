import os

def package_tile_downSampling_R(layer_num: int):
    """
    修改後的 Right Branch DownSampling 打包邏輯：
    1. Filter: 總共輸出 24 個 Group (Group0.0 - Group5.3)。
    2. Bias: 總共輸出 6 個 Group (Bias0 - Bias5)，使用 Row-Base 順序。
    3. 合併儲存: 每個檔案內依序包含 PW1 -> DW -> PW2 的內容。
    
    參數:
        layer_num (int): 層級識別碼 (0, 4, 12)。
    """

    # --- 1. 驗證與路徑映射 ---
    valid_layers = {0, 4, 12}
    if layer_num not in valid_layers:
        raise ValueError(f"無效的 layer_num：{layer_num}。允許的值為：{valid_layers}")
    
    tile_map = {
        0: "tile1.2",
        4: "tile5.2",
        12: "tile13.2"
    }
    mapped_tile_name = tile_map[layer_num]

    # --- 2. 設定來源路徑 ---
    base_split = "output_data_split"
    # 右分支的三個來源：PW1, DW, PW2
    src_pw1 = os.path.join(base_split, "pw_column_filters", f"features.{layer_num}.banch2.0")
    src_dw  = os.path.join(base_split, "dw_column_filters", f"features.{layer_num}.banch2.3")
    src_pw2 = os.path.join(base_split, "pw_column_filters", f"features.{layer_num}.banch2.5")

    # --- 3. 設定輸出路徑 ---
    base_output_dir = os.path.join("output_data_packaged", f"{mapped_tile_name}_DownSamplingR")
    
    os.makedirs(base_output_dir, exist_ok=True)

    print(f"已確認輸出目錄：{base_output_dir}")

    # --- 4. 取得並排序 Filter 索引 ---
    try:
        all_files = [f for f in os.listdir(src_pw1) if f.startswith("Filter") and f.endswith(".txt")]
    except FileNotFoundError:
        print(f"錯誤：找不到來源目錄 {src_pw1}")
        return

    # 提取數字並排序
    filter_indices = []
    for f in all_files:
        try:
            idx = int(f.replace("Filter", "").replace(".txt", ""))
            filter_indices.append(idx)
        except ValueError:
            continue
    filter_indices.sort()
    
    # 建立一個 Set 加速查找 (用於 Bias 階段確認 index 是否存在)
    filter_indices_set = set(filter_indices)
    
    total_files = len(filter_indices)
    print(f"偵測到 {total_files} 個 Filter，開始打包...")

    # ==========================================
    # --- 5. 處理 Filter (24 Groups) - [保持原樣] ---
    # ==========================================
    print("--- 正在處理 Filter (24 Groups) ---")
    
    for slot_idx in range(24):
        # 計算 Group 名稱
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Group{major_group}.{minor_group}.txt"

        # 找出屬於這個 Slot 的所有 Filter Index (間隔 24)
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

        # 寫入檔案 (合併 PW1, DW, PW2)
        if content_pw1: 
            text_pw1 = "\n\n".join(content_pw1)
            text_dw  = "\n\n".join(content_dw)
            text_pw2 = "\n\n".join(content_pw2)

            with open(os.path.join(base_output_dir, output_filename), 'w', encoding='utf-8') as f:
                f.write(text_pw1)
                f.write("\n\n\n") # 分隔線
                f.write(text_dw)
                f.write("\n\n\n") # 分隔線
                f.write(text_pw2)
                f.write("\n")
        
            # 顯示進度
            indices_str = ", ".join([str(i) for i in target_indices])
            print(f"  已生成 {output_filename} \t包含 Filter: [{indices_str}]")

    # ==========================================
    # --- 6. 處理 Bias (6 Major Groups) - [修改為 Row Base] ---
    # ==========================================
    print("\n--- 正在處理 Bias (6 Major Groups - Row Base) ---")
    
    # 計算最大深度 (例如 76 個檔案 -> 76/24 = 3...4 -> max_depth = 4)
    max_depth = (total_files + 23) // 24

    for major_group in range(6):
        output_filename = f"Bias{major_group}.txt"
        
        content_pw1 = []
        content_dw  = []
        content_pw2 = []
        collected_indices = []

        # 該 Major Group 包含的基礎 Slot (例如 Group 0 -> [0, 1, 2, 3])
        base_slots = [major_group * 4 + i for i in range(4)]

        # [核心修改]: 巢狀迴圈順序改變
        # 1. 外層 Loop: Depth (0, 1, 2...) 對應偏移量 (0, 24, 48...)
        # 2. 內層 Loop: Slot (0, 1, 2, 3)
        # 這樣就能達成 [0, 1, 2, 3, 24, 25, 26, 27...] 的順序
        
        for depth in range(max_depth):
            offset = depth * 24
            for slot_idx in base_slots:
                target_idx = offset + slot_idx
                
                # 確認此 index 是否存在於原始檔案清單中
                if target_idx in filter_indices_set:
                    collected_indices.append(target_idx)
                    
                    fname = f"Bias{target_idx}.txt" # 注意這裡是讀取 Bias 檔名
                    
                    p_pw1 = os.path.join(src_pw1, fname)
                    p_dw  = os.path.join(src_dw, fname)
                    p_pw2 = os.path.join(src_pw2, fname)
                    
                    try:
                        with open(p_pw1, 'r', encoding='utf-8') as f: content_pw1.append(f.read().strip())
                        with open(p_dw,  'r', encoding='utf-8') as f: content_dw.append(f.read().strip())
                        with open(p_pw2, 'r', encoding='utf-8') as f: content_pw2.append(f.read().strip())
                    except FileNotFoundError:
                        # Bias 檔案有時可能不存在，選擇忽略
                        pass

        # 寫入 Bias 輸出檔案
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
            
            # 顯示前幾個 Index 驗證順序
            display_indices = collected_indices[:16]
            indices_str = ", ".join(map(str, display_indices))
            if len(collected_indices) > 16:
                indices_str += " ..."
            print(f"  已生成 {output_filename} \t包含 Bias: [{indices_str}]")

    print("全部打包完成。")

# --- 測試執行區塊 ---
if __name__ == "__main__":
    try:
        # 測試 layer 12
        package_tile_downSampling_R(4)
    except Exception as e:
        print(f"執行錯誤: {e}")