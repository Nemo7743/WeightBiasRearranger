import os

def package_tile_downSampling_R(layer_num: int):
    """
    修改後的 Right Branch DownSampling 打包邏輯：
    1. 總共輸出 24 個 Group (Group0.0 - Group5.3)。
    2. PW1, DW, PW2 分開存放在三個不同資料夾 (P0_PW, P1_DW, P2_PW)。
    3. 若 Filter 數量 > 24，則進行堆疊 (例如 Group0.0 包含 Filter0 + Filter24)。
    
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
    # [修改點 1] 建立新的根目錄與三個子目錄
    base_output_dir = os.path.join("output_data_packaged", f"{mapped_tile_name}_DownSamplingR")
    
    dir_p0 = os.path.join(base_output_dir, "P0_PW")
    dir_p1 = os.path.join(base_output_dir, "P1_DW")
    dir_p2 = os.path.join(base_output_dir, "P2_PW")

    for d in [dir_p0, dir_p1, dir_p2]:
        os.makedirs(d, exist_ok=True)

    print(f"已確認輸出目錄結構於：{base_output_dir}")
    print(f"  -> P0_PW, P1_DW, P2_PW")

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
    
    total_files = len(filter_indices)
    print(f"偵測到 {total_files} 個 Filter，正在進行 24 分組打包 (PW/DW 分離)...")

    # --- 5. 核心打包迴圈 (24 Groups) ---
    # 我們需要產生 24 個輸出檔，對應硬體的 24 個位置
    
    for slot_idx in range(24):
        # 計算 Group 名稱
        major_group = slot_idx // 4
        minor_group = slot_idx % 4
        output_filename = f"Group{major_group}.{minor_group}.txt"

        # 找出屬於這個 Slot 的所有 Filter Index (間隔 24)
        # 例如 slot 0 會抓到 0, 24, 48...
        target_indices = [idx for idx in filter_indices if idx % 24 == slot_idx]
        
        # 準備容器
        content_p0 = [] # 用於 P0_PW
        content_p1 = [] # 用於 P1_DW
        content_p2 = [] # 用於 P2_PW

        for idx in target_indices:
            fname = f"Filter{idx}.txt"
            
            # 定義三個檔案的完整路徑
            p_pw1 = os.path.join(src_pw1, fname)
            p_dw  = os.path.join(src_dw, fname)
            p_pw2 = os.path.join(src_pw2, fname)
            
            try:
                # 讀取三個檔案
                with open(p_pw1, 'r', encoding='utf-8') as f: content_p0.append(f.read().strip())
                with open(p_dw,  'r', encoding='utf-8') as f: content_p1.append(f.read().strip())
                with open(p_pw2, 'r', encoding='utf-8') as f: content_p2.append(f.read().strip())
            except FileNotFoundError:
                print(f"  [警告] Filter{idx} 的部分檔案遺失，跳過此 Filter。")

        # --- 6. 寫入檔案 (三個資料夾各寫一份) ---
        if content_p0: # 只要有內容就寫入 (三者長度應相同)
            
            # 使用雙換行連接堆疊的 Filter
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
    try:
        # 測試 layer 0 -> 應輸出到 tile1.2_DownSamplingR
        package_tile_downSampling_R(12)
    except Exception as e:
        print(f"執行錯誤: {e}")