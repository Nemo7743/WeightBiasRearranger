import os

def package_tile_downSampling_L(layer_num: int):
    """
    準備目錄路徑，驗證輸入，並將 ShuffleNet 權重打包成分組的文字檔案。
    
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

    # 保留特定的目錄命名慣例
    dw_folder_name = f"features.{layer_num}.banch1.0"
    pw_folder_name = f"features.{layer_num}.banch1.2"

    dw_source_path = os.path.join("output_data_split", "dw_column_filters", dw_folder_name)
    pw_source_path = os.path.join("output_data_split", "pw_column_filters", pw_folder_name)
    output_path = os.path.join("output_data_packaged", mapped_tile_name)

    # 確保輸出目錄存在
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"已建立輸出目錄：{output_path}")

    # --- 3. 檔案搜尋與數值排序 ---
    try:
        # 僅列出 .txt 檔案
        all_files = [f for f in os.listdir(dw_source_path) if f.endswith(".txt")]
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到來源目錄：{dw_source_path}")

    # 關鍵：依數字排序 (Filter2 < Filter10)，而非依字母順序
    # 我們假設檔名格式為 'FilterX.txt'
    all_files.sort(key=lambda x: int(x.replace("Filter", "").replace(".txt", "")))
    
    total_files = len(all_files)
    if total_files == 0:
        print("警告：來源目錄中未發現過濾器檔案。")
        return dw_source_path, pw_source_path, output_path

    # --- 4. 動態分組邏輯 ---
    # 我們需要正好 6 個輸出檔案 (Group0 - Group5)
    # 計算基礎區塊大小
    chunk_size = total_files // 6
    
    # 如果 total_files < 6，chunk_size 會是 0。
    # 下方的邏輯會處理 0 的情況，將所有檔案放入 Group 5 或建立空群組。
    
    print(f"正在將 {total_files} 個過濾器處理分為 6 組...")

    for group_idx in range(6):
        # 計算切片的起始與結束索引
        start_idx = group_idx * chunk_size
        
        # 處理餘數的邏輯：
        # 如果是最後一組 (Group 5)，則納入剩餘的所有檔案。
        # 這確保當 total_files 不能被 6 整除時，不會有檔案被遺漏。
        if group_idx == 5:
            group_files = all_files[start_idx:]
        else:
            end_idx = start_idx + chunk_size
            group_files = all_files[start_idx:end_idx]

        # --- 5. 內容處理 (迴圈) ---
        combined_content = []
        
        for filename in group_files:
            # 建構完整路徑
            dw_file_path = os.path.join(dw_source_path, filename)
            pw_file_path = os.path.join(pw_source_path, filename)

            # 讀取 DW 內容
            with open(dw_file_path, 'r', encoding='utf-8') as f:
                dw_content = f.read().strip()

            # 讀取 PW 內容
            with open(pw_file_path, 'r', encoding='utf-8') as f:
                pw_content = f.read().strip()

            # 格式化配對：dw \n pw
            pair_block = f"{dw_content}\n\n{pw_content}"
            combined_content.append(pair_block)

        # 將此群組中的所有配對用雙換行符號連接
        final_group_string = "\n\n\n".join(combined_content)

        # --- 6. 輸出生成 ---
        output_filename = f"Group{group_idx}.txt"
        output_file_path = os.path.join(output_path, output_filename)

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(final_group_string)
            
        print(f"  已生成 {output_filename}，包含 {len(group_files)} 組配對。")

    print("打包完成。")
    return dw_source_path, pw_source_path, output_path

# --- 測試執行區塊 ---
if __name__ == "__main__":
    # 注意：此區塊假設目錄結構/檔案存在才能成功執行。
    # 這僅是示範如何呼叫此函數。
    try:
        src_dw, src_pw, dst = package_tile_downSampling_L(12)
        print(f"\n已驗證路徑：\nDW 來源：{src_dw}\nPW 來源：{src_pw}\n輸出：{dst}")
    except Exception as e:
        print(f"錯誤：{e}")