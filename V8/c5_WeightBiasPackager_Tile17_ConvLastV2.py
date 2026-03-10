import os
import math

def package_tile17_convlast():
    """
    修改後的 Conv Last 打包邏輯：
    1. Filter: 輸出 24 個 Group。
       邏輯變更: 採 Block Base (每 4 個 Group 一組填滿後再填下一組)，內部間隔為 4。
    2. Bias:   已修改為與 Filter 相同，輸出 24 個 Group，邏輯同上。
    3. 補零:   自動計算補零數量以符合 24 的倍數 (支援 960 及 1024)。
    """
    
    # --- 1. 路徑設定 ---
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, 'output_data_split', 'conv_last_filters')
    
    # 輸出路徑
    output_dir = os.path.join(base_dir, 'output_data_packaged', 'tile17_ConvLast_FC')

    # 建立目錄
    os.makedirs(output_dir, exist_ok=True)
    print(f"已確認輸出目錄：{output_dir}")

    # --- 2. 參數設定 (動態計算) ---
    TOTAL_GROUPS = 24             # Filter 分 24 包
    
    # 偵測實際檔案數量 (以 Filter 為主)
    try:
        all_filters = [f for f in os.listdir(input_dir) if f.startswith("Filter") and f.endswith(".txt")]
        TOTAL_REAL_FILTERS = len(all_filters)
    except FileNotFoundError:
        print(f"錯誤：找不到來源目錄 {input_dir}")
        return

    # 計算需要的虛擬總數 (向上取 24 的倍數)
    # 例如: 960 -> 960, 1024 -> 1032
    if TOTAL_REAL_FILTERS > 0:
        TOTAL_VIRTUAL_SLOTS = math.ceil(TOTAL_REAL_FILTERS / TOTAL_GROUPS) * TOTAL_GROUPS
    else:
        TOTAL_VIRTUAL_SLOTS = TOTAL_GROUPS # 避免除以零，至少預設一輪

    items_per_group = TOTAL_VIRTUAL_SLOTS // TOTAL_GROUPS

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

    # [Bias 樣板]
    ref_bias_file = os.path.join(input_dir, 'Bias0.txt')
    zero_bias_content = "00000000" # 預設值
    if os.path.exists(ref_bias_file):
         with open(ref_bias_file, 'r', encoding='utf-8') as f:
            # 這裡簡單假設使用標準8碼0
            zero_bias_content = "00000000"

    print(f"正在處理 {TOTAL_VIRTUAL_SLOTS} 個單元 (實體 {TOTAL_REAL_FILTERS} + 補零 {TOTAL_VIRTUAL_SLOTS - TOTAL_REAL_FILTERS})...")
    print(f"每組 Group 分配 {items_per_group} 個檔案。")

    # ==========================================
    # --- 4. Filter 打包 (Block Base) ---
    # ==========================================
    print("--- 正在處理 Filter (Block Base) ---")
    
    for slot_idx in range(TOTAL_GROUPS):
        
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Weight{major_group}.{minor_group}.txt"
        
        # [修改邏輯]: Block Base 索引計算
        # 1. 該 Row (Major Group) 負責的總容量 = items_per_group * 4
        # 2. 該 Row 的起始 Index = major_group * row_capacity
        # 3. 加上 minor_group 偏移，並在該 Row 範圍內以 4 為間隔取值
        
        row_capacity = items_per_group * 4
        base_index_pos = (major_group * row_capacity) + minor_group
        
        group_indices = []
        for k in range(items_per_group):
            idx = base_index_pos + (k * 4)
            group_indices.append(idx)
        
        group_content_list = []

        for current_filter_num in group_indices:
            
            if current_filter_num < TOTAL_REAL_FILTERS:
                file_path = os.path.join(input_dir, f'Filter{current_filter_num}.txt')
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        group_content_list.append(f.read().strip())
                else:
                    # 雖然在 REAL 範圍內但檔案遺失
                    print(f"  [警告] 找不到實體檔案 Filter{current_filter_num}，以全0取代。")
                    group_content_list.append(zero_filter_content)
            else:
                # 補零區域 (大於 REAL，小於 VIRTUAL)
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
    # --- 5. Bias 打包 (Block Base) ---
    # ==========================================
    print("\n--- 正在處理 Bias (Block Base) ---")
    
    # [修改邏輯]: Bias 使用與 Filter 完全相同的 Block Base 邏輯
    for slot_idx in range(TOTAL_GROUPS):
        
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Bias{major_group}.{minor_group}.txt"
        
        # 使用相同的索引計算邏輯
        row_capacity = items_per_group * 4
        base_index_pos = (major_group * row_capacity) + minor_group
        
        group_indices = []
        for k in range(items_per_group):
            idx = base_index_pos + (k * 4)
            group_indices.append(idx)
        
        content_list = []
        collected_indices = [] # 用於顯示實際包含的 index
        
        for current_bias_num in group_indices:
            
            collected_indices.append(current_bias_num)
            
            if current_bias_num < TOTAL_REAL_FILTERS:
                file_path = os.path.join(input_dir, f'Bias{current_bias_num}.txt')
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_list.append(f.read().strip())
                else:
                    # Bias 實體檔案遺失時補零
                    content_list.append(zero_bias_content)
            else:
                # 虛擬補零區
                content_list.append(zero_bias_content)

        # 寫入檔案 
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