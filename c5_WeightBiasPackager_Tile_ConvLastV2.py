import os

def package_tile_convlast():
    """
    將 Conv Last 層的 Filter 打包成 6 個分組 (Group0 - Group5)。
    採用間隔採樣 (Interleaved) 方式，Step=6。
    若 Index 超過 1023 (原始檔案上限)，則自動補零。
    """
    # --- 設定路徑 ---
    base_dir = os.getcwd()  # 取得目前工作目錄
    input_dir = os.path.join(base_dir, 'output_data_split', 'conv_last_filters')
    output_dir = os.path.join(base_dir, 'output_data_packaged', 'tile17')

    # 確保輸出目錄存在，若無則建立
    os.makedirs(output_dir, exist_ok=True)
    
    # [修改點 1] 提早確認輸出目錄
    print(f"已確認輸出目錄：{output_dir}")

    # --- 設定參數 ---
    FILES_PER_GROUP = 172       # 每一包必須有 172 個 Filter
    TOTAL_GROUPS = 6            # 固定輸出 6 包
    TOTAL_REAL_FILTERS = 1024   # 只有 0 ~ 1023 是真實存在的檔案
    
    # 計算虛擬總 Slot 數 (應該是 1032)
    TOTAL_VIRTUAL_SLOTS = FILES_PER_GROUP * TOTAL_GROUPS 

    # --- 步驟 1: 建立全 0 的 Filter 樣板 (Zero Template) ---
    ref_file = os.path.join(input_dir, 'Filter0.txt')
    zero_filter_content = ""
    
    if os.path.exists(ref_file):
        with open(ref_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            zero_lines = ["0000 0000 0000 0000" for _ in lines]
            zero_filter_content = "\n".join(zero_lines)
    else:
        # print("警告: 找不到 Filter0.txt 作為樣板，將使用預設 49 行全零格式。") # 保持版面乾淨可註解
        zero_lines = ["0000 0000 0000 0000"] * 49
        zero_filter_content = "\n".join(zero_lines)

    # [修改點 2] 顯示總體處理狀態
    print(f"正在將 {TOTAL_VIRTUAL_SLOTS} 個過濾器分散處理為 {TOTAL_GROUPS} 組...")

    # --- 步驟 2: 執行分散分組 (Interleaved) ---
    # 規則：Group N 負責 indices [N, N+6, N+12, ...]
    
    for group_idx in range(TOTAL_GROUPS):
        group_content_list = []
        
        # 產生該 Group 負責的所有 Index (間隔為 6)
        # 這裡會產生 range 物件，例如 range(0, 1032, 6)
        group_indices = range(group_idx, TOTAL_VIRTUAL_SLOTS, TOTAL_GROUPS)
        
        # 轉換為 list 以便後續操作與顯示
        group_indices_list = list(group_indices)
        
        # 確保該組數量正確 (除錯用，可保留或註解)
        if len(group_indices_list) != FILES_PER_GROUP:
             print(f"警告：Group{group_idx} 分配到的數量 ({len(group_indices_list)}) 不等於預期的 {FILES_PER_GROUP}")

        # 遍歷該組分配到的 Index
        for current_filter_num in group_indices_list:
            file_path = os.path.join(input_dir, f'Filter{current_filter_num}.txt')
            
            content = ""
            
            # 判斷邏輯：Index < 1024 且檔案存在
            if current_filter_num < TOTAL_REAL_FILTERS and os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
            else:
                # 超出範圍或檔案遺失 -> 填入全 0
                content = zero_filter_content

            group_content_list.append(content)

        # 將該組所有 Filter 用兩個換行符號連接
        full_group_text = "\n\n".join(group_content_list)

        # 寫入 GroupX.txt
        output_filename = f'Group{group_idx}.txt'
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(full_group_text)
            
        # [修改點 3] 調整縮排與顯示格式
        # 由於列表很長 (172個)，為了美觀，顯示格式為 [0, 6, 12, ..., 1026]
        first_few = ", ".join(map(str, group_indices_list[:3])) # 前三個
        last_one = group_indices_list[-1]                       # 最後一個
        print(f"  已生成 {output_filename}，包含 Filter: [{first_few}, ..., {last_one}]")

    # [修改點 4] 簡化結束訊息
    print("打包完成。")

# 執行函式
if __name__ == "__main__":
    package_tile_convlast()