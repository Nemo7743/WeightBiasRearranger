import os

def package_tile_downSampling_R(layer_num: int):
    """
    修改後的 Right Branch DownSampling 打包邏輯：
    1. Filter: 總共輸出 24 個 Group (Group0.0 - Group5.3)。
       邏輯變更：平均分配總數後，採 Block Base 方式 (每 4 個 Group 一組填滿後再填下一組)。
    2. Bias:   已修改為與 Filter 相同，輸出 24 個 Group (Bias0.0 - Bias5.3)，邏輯同上。
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
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Weight{major_group}.{minor_group}.txt"

        # [修改邏輯] 計算目標索引 (Block Base)
        # 1. 每個 Row (Major Group) 負責處理的數量 = items_per_group * 4
        # 2. 該 Row 的起始位置 = major_group * row_capacity
        # 3. 加上 minor_group 偏移，並在區塊內以 4 為間隔取值
        
        row_capacity = items_per_group * 4
        base_index_pos = (major_group * row_capacity) + minor_group
        
        target_indices = []
        for k in range(items_per_group):
            # 計算在 filter_indices 列表中的位置
            list_pos = base_index_pos + (k * 4)
            
            # 確保不超出範圍 (處理整除餘數情況)
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
    # --- 6. 處理 Bias (24 Groups) - [修改為 Block Base] ---
    # ==========================================
    print("\n--- 正在處理 Bias (24 Groups - Column Base) ---")
    
    # [修改邏輯]: 使用與 Filter 完全相同的計算邏輯
    for slot_idx in range(TOTAL_GROUPS):
        # 計算 Group 名稱 (使用 BiasX.Y 格式以區分)
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Bias{major_group}.{minor_group}.txt"

        # [修改邏輯] 重複使用 Filter 的索引計算方式
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
        
        # 收集成功讀取的 index 以便顯示
        collected_indices = []

        for idx in target_indices:
            fname = f"Bias{idx}.txt" # 讀取 Bias 檔名
            
            p_pw1 = os.path.join(src_pw1, fname)
            p_dw  = os.path.join(src_dw, fname)
            p_pw2 = os.path.join(src_pw2, fname)
            
            try:
                # 嘗試讀取三個檔案
                with open(p_pw1, 'r', encoding='utf-8') as f: content_pw1.append(f.read().strip())
                with open(p_dw,  'r', encoding='utf-8') as f: content_dw.append(f.read().strip())
                with open(p_pw2, 'r', encoding='utf-8') as f: content_pw2.append(f.read().strip())
                collected_indices.append(idx)
            except FileNotFoundError:
                # Bias 檔案有時可能不存在，選擇忽略
                pass

        # 寫入 Bias 輸出檔案
        if content_pw1:
            # 為了與 Weight 邏輯保持一致，這裡使用 \n\n 拼接
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
            
            # 顯示進度
            indices_str = ", ".join(map(str, collected_indices))
            print(f"  已生成 {output_filename} \t包含 Bias: [{indices_str}]")

    print("全部打包完成。")

# --- 測試執行區塊 ---
if __name__ == "__main__":
    try:
        # 測試 layer 4
        package_tile_downSampling_R(0)
    except Exception as e:
        print(f"執行錯誤: {e}")