import os
import math

def package_tile_downSampling_R(layer_num):
    """
    將來自三個來源目錄的權重打包成 6 個分組的輸出檔案，
    用於右分支 (Right Branch) 下採樣邏輯。
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
    
    # [修改點 1] 在建立目錄後，印出確認路徑
    print(f"已確認輸出目錄：{output_dir}")

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
                index = int(f[6:-4]) 
                filter_indices.append(index)
            except ValueError:
                continue

    # 關鍵：依數值排序
    filter_indices.sort()
    
    total_filters = len(filter_indices)
    if total_filters == 0:
        print(f"警告：在 {src_pw1} 中找不到有效的過濾器檔案")
        return

    # --- 第三階段：分散式分組 (Interleaved Grouping) 與處理 ---
    
    num_groups = 6
    
    # [修改點 2] 在開始迴圈前，印出總體處理狀態
    print(f"正在將 {total_filters} 個過濾器分散處理為 {num_groups} 組...")

    for group_idx in range(num_groups):
        current_group_indices = filter_indices[group_idx::num_groups]
        
        if not current_group_indices:
            # 若該組無分配到 filter (視需求決定是否印出，這裡保持簡潔略過或印出提示)
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
                raise FileNotFoundError(f"Filter{idx} 缺少對應的檔案：{e.filename}")

            # 組合：PW1 \n\n DW \n\n PW2
            combined_block = f"{content_pw1}\n\n{content_dw}\n\n{content_pw2}"
            group_content_blocks.append(combined_block)

        # --- 第四階段：寫入輸出 ---

        final_group_content = "\n\n\n".join(group_content_blocks)
        
        output_filename = f"Group{group_idx}.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_group_content)
        
        # [修改點 3] 修改縮排與顯示格式
        indices_str = ", ".join(map(str, current_group_indices))
        print(f"  已生成 {output_filename}，包含 Filter: [{indices_str}]")

    # [修改點 4] 簡化結束訊息
    print("打包完成。")

# --- 測試執行區塊 ---
if __name__ == "__main__":
    # 測試範例
    # 注意：這裡會依據程式邏輯輸出到 tile1.2 (因為是 Right Branch)，
    # 但格式會完全符合您要求的樣式。
    package_tile_downSampling_R(0)