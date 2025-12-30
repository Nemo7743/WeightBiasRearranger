import os

def package_tile_downSampling_L(layer_num: int):
    """
    修改後的 DownSampling 打包邏輯：
    1. 總共輸出 24 個 Group (Group0.0 - Group5.3)。
    2. DW 與 PW 分開存放在不同資料夾 (P0_DW, P1_PW)。
    3. 若 Filter 數量 > 24，則進行堆疊 (例如 Group0.0 包含 Filter0 + Filter24)。
    
    參數:
        layer_num (int): 層級識別碼 (0, 4, 12)。
    """
    
    # --- 1. 參數驗證 ---
    valid_layers = {0, 4, 12}
    if layer_num not in valid_layers:
        raise ValueError(f"無效的 layer_num：{layer_num}。允許的值為：{valid_layers}")

    # --- 2. 路徑設定 ---
    tile_map = {
        0: "tile1.1",
        4: "tile5.1",
        12: "tile13.1"
    }
    mapped_tile_name = tile_map[layer_num]

    # 原始來源資料夾 (Left Branch)
    dw_folder_name = f"features.{layer_num}.banch1.0"
    pw_folder_name = f"features.{layer_num}.banch1.2"

    dw_source_dir = os.path.join("output_data_split", "dw_column_filters", dw_folder_name)
    pw_source_dir = os.path.join("output_data_split", "pw_column_filters", pw_folder_name)
    
    # [修改點 1] 設定新的輸出根目錄結構
    base_output_dir = os.path.join("output_data_packaged", f"{mapped_tile_name}_DownSamplingL")
    
    # 建立 P0_DW 和 P1_PW 兩個子目錄
    dw_output_dir = os.path.join(base_output_dir, "P0_DW")
    pw_output_dir = os.path.join(base_output_dir, "P1_PW")

    os.makedirs(dw_output_dir, exist_ok=True)
    os.makedirs(pw_output_dir, exist_ok=True)
    
    print(f"已確認輸出目錄：\n  DW -> {dw_output_dir}\n  PW -> {pw_output_dir}")

    # --- 3. 讀取並排序來源檔案 ---
    try:
        # 讀取 DW 目錄下的所有 Filter 檔案
        all_files = [f for f in os.listdir(dw_source_dir) if f.endswith(".txt")]
    except FileNotFoundError:
        print(f"錯誤：找不到來源目錄 {dw_source_dir}")
        return

    # 依據數字大小排序 (Filter0, Filter1, ... Filter24)
    all_files.sort(key=lambda x: int(x.replace("Filter", "").replace(".txt", "")))
    total_files = len(all_files)
    
    print(f"偵測到 {total_files} 個 Filter，正在進行 24 分組打包...")

    # --- 4. 核心打包邏輯 (24 Groups) ---
    # 我們需要產生 24 個輸出檔：Group0.0 到 Group5.3
    # 對應關係：
    # Slot 0  (Group0.0) -> Filter 0, 24, 48...
    # Slot 1  (Group0.1) -> Filter 1, 25, 49...
    # Slot 23 (Group5.3) -> Filter 23, 47, 71...
    
    for slot_idx in range(24):
        # 計算 Group 名稱
        major_group = slot_idx // 4  # 0~5
        minor_group = slot_idx % 4   # 0~3
        output_filename = f"Group{major_group}.{minor_group}.txt"

        # 找出屬於這個 Slot 的所有 Filter Index
        # 使用 range(start, stop, step) -> 從 slot_idx 開始，每次跳 24
        target_indices = list(range(slot_idx, total_files, 24))
        
        # 準備容器儲存內容
        dw_content_list = []
        pw_content_list = []
        
        # 讀取對應的 Filter 檔案
        for filter_idx in target_indices:
            filename = f"Filter{filter_idx}.txt"
            
            dw_path = os.path.join(dw_source_dir, filename)
            pw_path = os.path.join(pw_source_dir, filename)
            
            try:
                # 讀取 DW
                with open(dw_path, 'r', encoding='utf-8') as f:
                    dw_content_list.append(f.read().strip())
                
                # 讀取 PW
                with open(pw_path, 'r', encoding='utf-8') as f:
                    pw_content_list.append(f.read().strip())
                    
            except FileNotFoundError:
                print(f"  [警告] 檔案遺失：{filename} (跳過)")

        # --- 5. 寫入輸出檔案 (DW 與 PW 分開寫) ---
        
        # 只有當有內容時才寫入
        if dw_content_list:
            # 合併內容，中間用雙換行隔開
            final_dw_text = "\n\n".join(dw_content_list)
            final_pw_text = "\n\n".join(pw_content_list)
            
            # 寫入 DW Group 檔案
            with open(os.path.join(dw_output_dir, output_filename), 'w', encoding='utf-8') as f_dw:
                f_dw.write(final_dw_text)

            # 寫入 PW Group 檔案
            with open(os.path.join(pw_output_dir, output_filename), 'w', encoding='utf-8') as f_pw:
                f_pw.write(final_pw_text)
            
            # 顯示進度
            indices_str = ", ".join([str(i) for i in target_indices])
            print(f"  已生成 {output_filename} \t包含 Filter: [{indices_str}]")

    print("打包完成。")

# --- 測試執行 ---
if __name__ == "__main__":
    # 請確保資料夾結構存在以進行測試
    try:
        package_tile_downSampling_L(0) 
    except Exception as e:
        print(f"執行中發生錯誤: {e}")