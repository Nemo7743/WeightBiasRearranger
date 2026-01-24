import os

def package_tile_OGshuffle(layer_num):
    """
    修改後的 ShuffleNet (OG Shuffle) 打包邏輯：
    1. 總共輸出 24 個 Group (Group0.0 - Group5.3)。
    2. 三個分支 (PW1, DW, PW2) 分開存放在不同資料夾 (P0_PW, P1_DW, P2_PW)。
    3. 若 Filter 數量 > 24，則進行堆疊 (例如 Group0.0 包含 Filter0 + Filter24)。
    
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
    # [修改點 1] 建立新的根目錄與三個子目錄
    base_output_dir = os.path.join("output_data_packaged", f"{tile_name}_OGShuffle")
    
    dir_p0 = os.path.join(base_output_dir, "P0_PW")
    dir_p1 = os.path.join(base_output_dir, "P1_DW")
    dir_p2 = os.path.join(base_output_dir, "P2_PW")

    # 建立目錄
    for d in [dir_p0, dir_p1, dir_p2]:
        os.makedirs(d, exist_ok=True)

    print(f"已確認輸出目錄結構於：{base_output_dir}")
    print("  -> 分離為: P0_PW, P1_DW, P2_PW")

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
            idx = int(f[6:-4])
            filter_indices.append(idx)
        except ValueError:
            continue
    filter_indices.sort()
    
    total_files = len(filter_indices)
    print(f"偵測到 {total_files} 個 Filter，正在進行 24 分組打包 (三路分離)...")

    # --- 5. 核心打包迴圈 (24 Groups) ---
    # 我們需要產生 24 個輸出檔 (Slot 0 ~ 23)
    
    for slot_idx in range(24):
        # 計算 Group 名稱
        major_group = slot_idx // 4  # 0~5
        minor_group = slot_idx % 4   # 0~3
        output_filename = f"Group{major_group}.{minor_group}.txt"

        # [修改點 2] 找出屬於這個 Slot 的所有 Filter Index
        # 邏輯：每隔 24 個取一個 (例如 slot 0 取 0, 24, 48...)
        target_indices = [idx for idx in filter_indices if idx % 24 == slot_idx]
        
        # 準備三個容器，分別存不同 layer 類型的內容
        content_p0 = [] # PW1
        content_p1 = [] # DW
        content_p2 = [] # PW2

        for idx in target_indices:
            fname = f"Filter{idx}.txt"
            
            # 定義三個來源檔案路徑
            p_pw1 = os.path.join(src_pw1, fname)
            p_dw  = os.path.join(src_dw, fname)
            p_pw2 = os.path.join(src_pw2, fname)
            
            try:
                # 讀取三個檔案
                with open(p_pw1, 'r', encoding='utf-8') as f: content_p0.append(f.read().strip())
                with open(p_dw,  'r', encoding='utf-8') as f: content_p1.append(f.read().strip())
                with open(p_pw2, 'r', encoding='utf-8') as f: content_p2.append(f.read().strip())
            except FileNotFoundError:
                print(f"  [警告] Filter{idx} 的部分檔案遺失，跳過。")

        # --- 6. 寫入檔案 (分開寫入) ---
        
        # 只要有內容就寫入 (假設三者同步)
        if content_p0:
            
            # 使用雙換行連接堆疊的 Filter (例如 Filter0 \n\n Filter24)
            text_p0 = "\n\n".join(content_p0)
            text_p1 = "\n\n".join(content_p1)
            text_p2 = "\n\n".join(content_p2)

            # 寫入 P0_PW
            with open(os.path.join(dir_p0, output_filename), 'w', encoding='utf-8') as f:
                f.write(text_p0)
            
            # 寫入 P1_DW
            with open(os.path.join(dir_p1, output_filename), 'w', encoding='utf-8') as f:
                f.write(text_p1)

            # 寫入 P2_PW
            with open(os.path.join(dir_p2, output_filename), 'w', encoding='utf-8') as f:
                f.write(text_p2)

            # 顯示進度
            indices_str = ", ".join(map(str, target_indices))
            print(f"  已生成 {output_filename} \t包含: [{indices_str}]")

    print("打包完成。")

# --- 測試執行區塊 ---
if __name__ == "__main__":
    # 測試執行 Layer 1
    # 依照你的 map，這會輸出到 output_data_packaged/tile2.2_OGShuffle
    layers_to_test = range(0, 16)
    
    for layer in layers_to_test:
        try:
            print(f"--- Processing Layer {layer} ---")
            package_tile_OGshuffle(layer)
            print("-" * 30)
        except Exception as e:
            print(f"Layer {layer} 執行失敗: {e}")