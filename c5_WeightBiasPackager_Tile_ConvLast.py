import os

def package_tile_convlast():
    # --- 設定路徑 ---
    base_dir = os.getcwd()  # 取得目前工作目錄
    input_dir = os.path.join(base_dir, 'output_data_split', 'conv_last_filters')
    output_dir = os.path.join(base_dir, 'output_data_packaged', 'tile17')

    # 確保輸出目錄存在，若無則建立
    os.makedirs(output_dir, exist_ok=True)

    # --- 設定參數 ---
    FILES_PER_GROUP = 172
    TOTAL_GROUPS = 6         # 預計輸出 Group0 到 Group5
    TOTAL_REAL_FILTERS = 1024 # 原始檔案只有 Filter0 到 Filter1023

    # --- 步驟 1: 建立全 0 的 Filter 樣板 (Zero Template) ---
    # 為了確保格式正確，我們讀取 Filter0 來決定全 0 Filter 應該長什麼樣子
    ref_file = os.path.join(input_dir, 'Filter0.txt')
    zero_filter_content = ""
    
    if os.path.exists(ref_file):
        with open(ref_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 根據讀取到的行數，建立對應行數的 "0000 0000 0000 0000"
            zero_lines = ["0000 0000 0000 0000" for _ in lines]
            zero_filter_content = "\n".join(zero_lines)
    else:
        # 如果找不到 Filter0，則使用預設值 (根據你的範例約為49行，這裡作為保險起見)
        print("警告: 找不到 Filter0.txt 作為樣板，將使用預設 49 行全零格式。")
        zero_lines = ["0000 0000 0000 0000"] * 49
        zero_filter_content = "\n".join(zero_lines)

    print(f"開始處理... 輸出路徑: {output_dir}")

    # --- 步驟 2: 執行分組與寫入 ---
    for group_idx in range(TOTAL_GROUPS):
        group_content_list = []
        start_filter_idx = group_idx * FILES_PER_GROUP
        
        # 遍歷這一組所需的 172 個 Filter
        for i in range(FILES_PER_GROUP):
            current_filter_num = start_filter_idx + i
            file_path = os.path.join(input_dir, f'Filter{current_filter_num}.txt')
            
            content = ""
            
            # 判斷是否為真實存在的 Filter (在 0~1023 範圍內 且 檔案存在)
            if current_filter_num < TOTAL_REAL_FILTERS and os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    # 使用 strip() 去除檔案頭尾多餘空白，確保合併時格式整齊
                    content = f.read().strip()
            else:
                # 超出範圍 (例如 Filter1024+) 或檔案遺失，填入全 0 樣板
                content = zero_filter_content
                # (Optional) Debug 訊息，若想知道哪些是補零的可以打開下面這行
                # print(f"Group{group_idx}: Filter{current_filter_num} 使用補零填充")

            group_content_list.append(content)

        # 將該組所有 Filter 用兩個換行符號連接
        full_group_text = "\n\n".join(group_content_list)

        # 寫入 GroupX.txt
        output_filename = os.path.join(output_dir, f'Group{group_idx}.txt')
        with open(output_filename, 'w', encoding='utf-8') as f_out:
            f_out.write(full_group_text)
            
        print(f"已生成: {output_filename} (包含 Filter {start_filter_idx} 到 {start_filter_idx + FILES_PER_GROUP - 1})")

    print("處理完成。")

# 執行函式
if __name__ == "__main__":
    package_tile_convlast()