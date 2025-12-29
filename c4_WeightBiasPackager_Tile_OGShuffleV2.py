import os
import math

def package_tile_OGshuffle(layer_num):
    """
    將來自三個來源目錄的權重打包成 6 個分組的輸出檔案，
    用於右分支 (Right Branch) 下採樣邏輯。

    修改說明：
    採用「間隔採樣 (Interleaved)」方式打包，確保固定輸出 6 個群組。
    使用 list slicing [start::6] 的方式，
    例如 Group0 包含 Filter 0, 6, 12, 18...
    這能確保在總數為 48 時，每包恰好有 8 個 filter，且分散於各區段。
    """
    # --- 第一階段：驗證與路徑設定 ---
    
    valid_layers = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]
    if layer_num not in valid_layers:
        print(f"無效的 layer_num。預期為 {valid_layers}。")
        raise ValueError(f"無效的 layer_num。預期為 {valid_layers}。")
    
    # 輸出路徑映射
    tile_map = {
        1: "tile2.2", 2: "tile3.2", 3: "tile4.2", 5: "tile6.2", 6: "tile7.2", 7: "tile8.2", 8: "tile9.2",
        9: "tile10.2", 10: "tile11.2", 11: "tile12.2", 13: "tile14.2", 14: "tile15.2", 15: "tile16.2"
                }
    tile_name = tile_map[layer_num]
    output_dir = os.path.join("output_data_packaged", tile_name)

    # 定義來源路徑
    base_split = "output_data_split"
    src_pw1 = os.path.join(base_split, "pw_column_filters", f"features.{layer_num}.banch2.0")
    src_dw  = os.path.join(base_split, "dw_column_filters", f"features.{layer_num}.banch2.3")
    src_pw2 = os.path.join(base_split, "pw_column_filters", f"features.{layer_num}.banch2.5")

    # 建立輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # [修改點 1] 提早確認輸出目錄
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
                # 提取 'Filter' 和 '.txt' 之間的數字
                index = int(f[6:-4]) 
                filter_indices.append(index)
            except ValueError:
                continue # 跳過不符合模式的檔案

    # 關鍵：依數值排序
    filter_indices.sort()
    
    total_filters = len(filter_indices)
    if total_filters == 0:
        print(f"警告：在 {src_pw1} 中找不到有效的過濾器檔案")
        return

    # --- 第三階段：動態分散分組 (Interleaved) 與處理 ---

    # 規則：必須固定打 6 包，且內容分散 (例如 0, 6, 12...)
    num_groups = 6

    # [修改點 2] 加入處理前的總結訊息
    print(f"正在將 {total_filters} 個過濾器分散處理為 {num_groups} 組...")

    for group_idx in range(num_groups):
        # 使用間隔切片：從 group_idx 開始，每隔 6 個取一個
        current_group_indices = filter_indices[group_idx::num_groups]
        
        # 如果沒有過濾器落入此群組，則跳過
        if not current_group_indices:
            # print(f"Group{group_idx} 無分配到 Filter，跳過。") # 可選：保持版面乾淨可註解掉
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
            combined_block = f"{content_pw1}\n\n{content_dw}\n\n{content_pw2}"
            group_content_blocks.append(combined_block)

        # --- 第四階段：寫入輸出 ---

        # 組合區塊：群組聚合 (三換行)
        final_group_content = "\n\n\n".join(group_content_blocks)
        
        output_filename = f"Group{group_idx}.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_group_content)
        
        # [修改點 3] 調整縮排與顯示格式 (只顯示檔名而非全路徑)
        indices_str = ", ".join(map(str, current_group_indices))
        print(f"  已生成 {output_filename}，包含 Filter: [{indices_str}]")

    # [修改點 4] 簡化完成訊息
    print("打包完成。")


# --- 測試執行區塊 ---
if __name__ == "__main__":
    # 這裡依序執行所有有效層級
    # 為了測試方便，這裡只先跑第一層 (Layer 1)
    # 若要跑全部，請取消下方 list 的註解並還原迴圈
    #layers_to_process = [1] 
    layers_to_process = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15]
    
    for layer in layers_to_process:
        try:
            print(f"--- Processing Layer {layer} ---")
            package_tile_OGshuffle(layer)
            print("-" * 30)
        except Exception as e:
            print(f"Layer {layer} 處理失敗: {e}")