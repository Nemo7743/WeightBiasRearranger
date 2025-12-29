import os
import math

def package_tile_downSampling_L(layer_num: int):
    """
    準備目錄路徑，驗證輸入，並將 ShuffleNet 權重打包成分組的文字檔案。
    
    修改說明：
    採用「間隔採樣 (Interleaved)」方式打包，確保固定輸出 6 個群組。
    使用 list slicing [start::6] 的方式，
    例如 Group0 包含 Filter 0, 6, 12, 18...
    這能確保在總數為 48 時，每包恰好有 8 個 filter，且分散於各區段。
    
    參數 (Args):
        layer_num (int): 層級識別碼。必須是 0, 4 或 12。
        
    回傳 (Returns):
        tuple: (dw_source_path, pw_source_path, output_path)
    """
    
    # --- 1. 驗證 ---
    valid_layers = {0, 4, 12}
    if layer_num not in valid_layers:
        raise ValueError(f"無效的 layer_num：{layer_num}。允許的值為：{valid_layers}")

    # --- 2. 路徑映射與設定 ---
    tile_map = {
        0: "tile1.1",
        4: "tile5.1",
        12: "tile13.1"
    }
    mapped_tile_name = tile_map[layer_num]

    # 保留特定的目錄命名慣例 (Left Branch)
    dw_folder_name = f"features.{layer_num}.banch1.0"
    pw_folder_name = f"features.{layer_num}.banch1.2"

    dw_source_path = os.path.join("output_data_split", "dw_column_filters", dw_folder_name)
    pw_source_path = os.path.join("output_data_split", "pw_column_filters", pw_folder_name)
    output_path = os.path.join("output_data_packaged", mapped_tile_name)

    # 確保輸出目錄存在
    os.makedirs(output_path, exist_ok=True)
    print(f"已確認輸出目錄：{output_path}")

    # --- 3. 檔案搜尋與數值排序 ---
    try:
        # 僅列出 .txt 檔案
        all_files = [f for f in os.listdir(dw_source_path) if f.endswith(".txt")]
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到來源目錄：{dw_source_path}")

    # 關鍵：依數字排序 (Filter2 < Filter10)，而非依字母順序
    all_files.sort(key=lambda x: int(x.replace("Filter", "").replace(".txt", "")))
    
    total_files = len(all_files)
    if total_files == 0:
        print("警告：來源目錄中未發現過濾器檔案。")
        return dw_source_path, pw_source_path, output_path

    # --- 4. 動態分組邏輯 (Interleaved) ---
    # 要求：必須固定打 6 包，且內容分散。
    # 算法：使用固定步長 6 進行切片。
    # Group 0: indices 0, 6, 12, 18...
    # Group 1: indices 1, 7, 13, 19...
    
    num_groups = 6
    print(f"正在將 {total_files} 個過濾器分散處理為 {num_groups} 組...")

    for group_idx in range(num_groups):
        # 使用 Python list slicing [start::step]
        # 這會自動處理所有長度，並均勻分配
        group_files = all_files[group_idx::num_groups]

        # 如果該組沒有分配到任何檔案 (例如總數少於 6 個時的後幾組)，則跳過或視需求處理
        if not group_files:
            continue

        # --- 5. 內容處理 (迴圈) ---
        combined_content = []
        
        for filename in group_files:
            # 建構完整路徑
            dw_file_path = os.path.join(dw_source_path, filename)
            pw_file_path = os.path.join(pw_source_path, filename)

            try:
                # 讀取 DW 內容
                with open(dw_file_path, 'r', encoding='utf-8') as f:
                    dw_content = f.read().strip()

                # 讀取 PW 內容
                with open(pw_file_path, 'r', encoding='utf-8') as f:
                    pw_content = f.read().strip()
                
                # 格式化配對：dw \n pw
                # 注意：這裡根據範例需求，DW 與 PW 之間用雙換行
                pair_block = f"{dw_content}\n\n{pw_content}"
                combined_content.append(pair_block)
                
            except FileNotFoundError as e:
                print(f"錯誤：找不到對應檔案 {e.filename}，跳過此 Filter。")
                continue

        # 將此群組中的所有配對用雙換行符號連接 (Filter 與 Filter 之間)
        final_group_string = "\n\n\n".join(combined_content)

        # --- 6. 輸出生成 ---
        output_filename = f"Group{group_idx}.txt"
        output_file_path = os.path.join(output_path, output_filename)

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(final_group_string)
            
        # 提取索引數字以顯示資訊
        indices = [f.replace("Filter", "").replace(".txt", "") for f in group_files]
        print(f"  已生成 {output_filename}，包含 Filter: [{', '.join(indices)}]")

    print("打包完成。")
    return dw_source_path, pw_source_path, output_path

# --- 測試執行區塊 ---
if __name__ == "__main__":
    # 注意：此區塊假設目錄結構/檔案存在才能成功執行。
    try:
        # 測試 layer_num = 12
        src_dw, src_pw, dst = package_tile_downSampling_L(11)
    except Exception as e:
        print(f"執行錯誤：{e}")