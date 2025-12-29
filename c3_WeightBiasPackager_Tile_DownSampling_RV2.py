import os
import math

def package_tile_downSampling_R(layer_num):
    """
    將來自三個來源目錄的權重打包成 6 個分組的輸出檔案，
    用於右分支 (Right Branch) 下採樣邏輯。
    
    修改重點：
    採用「間隔採樣」(Interleaved) 方式打包，
    例如：Group0 包含 0, 6, 12... 而非 0, 1, 2...
    確保固定輸出 6 個檔案。

    參數 (Args):
        layer_num (int): 層級索引。必須嚴格為 0, 4 或 12。

    拋出異常 (Raises):
        ValueError: 如果 layer_num 無效。
        FileNotFoundError: 如果來源檔案遺失。
    """
    # --- 第一階段：驗證與路徑設定 ---
    
    if layer_num not in [0, 4, 12]:
        print("無效的 layer_num。預期為 0、4 或 12。")
        raise ValueError("無效的 layer_num。預期為 0、4 或 12。")
    
    # 輸出路徑映射
    tile_map = {0: "tile1.2", 4: "tile5.2", 12: "tile13.2"}
    tile_name = tile_map[layer_num]
    output_dir = os.path.join("output_data_packaged", tile_name)

    # 定義來源路徑
    base_split = "output_data_split"
    src_pw1 = os.path.join(base_split, "pw_column_filters", f"features.{layer_num}.banch2.0")
    src_dw  = os.path.join(base_split, "dw_column_filters", f"features.{layer_num}.banch2.3")
    src_pw2 = os.path.join(base_split, "pw_column_filters", f"features.{layer_num}.banch2.5")

    # 建立輸出目錄
    os.makedirs(output_dir, exist_ok=True)

    # --- 第二階段：檔案搜尋與排序 ---

    # 掃描 src_pw1 以尋找所有過濾器索引
    try:
        all_files = os.listdir(src_pw1)
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到來源目錄：{src_pw1}")

    # 嚴格依照 'Filter{i}.txt' 格式提取索引
    filter_indices = []
    for f in all_files:
        if f.startswith("Filter") and f.endswith(".txt"):
            try:
                # 提取 'Filter' 和 '.txt' 之間的數字
                index = int(f[6:-4]) 
                filter_indices.append(index)
            except ValueError:
                print("存在不符合模式的檔案")
                continue # 跳過不符合模式的檔案

    # 關鍵：依數值排序，確保順序正確 (0, 1, 2, 3...)
    filter_indices.sort()
    
    total_filters = len(filter_indices)
    if total_filters == 0:
        print(f"警告：在 {src_pw1} 中找不到有效的過濾器檔案")
        return

    # --- 第三階段：分散式分組 (Interleaved Grouping) 與處理 ---

    # 規則：必須固定打 6 包，且內容分散
    # 使用 slicing [start::step] 的方式，Step 固定為 6
    # Group 0: indices[0], indices[6], indices[12]...
    # Group 1: indices[1], indices[7], indices[13]...
    
    num_groups = 6

    for group_idx in range(num_groups):
        # --- 修改點：使用間隔切片 (Step=6) ---
        # 這會自動處理所有長度的 filter 列表，並分配給 6 個組
        current_group_indices = filter_indices[group_idx::num_groups]
        
        # 如果因為 Filter 總數太少 (例如只有 4 個 filter)，導致後面的 Group 分不到 filter
        # 這種情況下 current_group_indices 會是空的，我們仍產生空檔案或跳過
        # 這裡選擇跳過不產生檔案，或者也可以產生空檔，視需求而定。
        # 根據一般邏輯，若無內容則不寫入：
        if not current_group_indices:
            print(f"Group{group_idx} 無分配到 Filter，跳過生成。")
            continue

        group_content_blocks = []

        # 處理此群組中的每個過濾器
        for idx in current_group_indices:
            filename = f"Filter{idx}.txt"
            
            path_pw1 = os.path.join(src_pw1, filename)
            path_dw  = os.path.join(src_dw, filename)
            path_pw2 = os.path.join(src_pw2, filename)

            # 從三個來源讀取內容
            try:
                with open(path_pw1, 'r', encoding='utf-8') as f:
                    content_pw1 = f.read().strip()
                with open(path_dw, 'r', encoding='utf-8') as f:
                    content_dw = f.read().strip()
                with open(path_pw2, 'r', encoding='utf-8') as f:
                    content_pw2 = f.read().strip()
            except FileNotFoundError as e:
                # 重新拋出異常並附帶上下文以協助除錯
                raise FileNotFoundError(f"Filter{idx} 缺少對應的檔案：{e.filename}")

            # 組合：內部區塊格式化 (雙換行)
            # 結構：PW1 \n\n DW \n\n PW2
            combined_block = f"{content_pw1}\n\n{content_dw}\n\n{content_pw2}"
            group_content_blocks.append(combined_block)

        # --- 第四階段：寫入輸出 ---

        # 組合區塊：群組聚合 (三換行)
        final_group_content = "\n\n\n".join(group_content_blocks)
        
        output_filename = f"Group{group_idx}.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_group_content)
        
        # 列印除錯訊息顯示該組包含哪些 Filter，方便確認分散是否正確
        indices_str = ", ".join(map(str, current_group_indices))
        print(f"已生成 {output_filename}，包含 Filter: [{indices_str}]")

    print(f"第 {layer_num} 層處理完成。輸出已儲存至 {output_dir}")

# --- 測試執行區塊 ---
if __name__ == "__main__":
    # 測試範例：確保 layer_num 為 0, 4, 或 12
    package_tile_downSampling_R(11)