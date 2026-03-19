import os

def update_tile17_ConvLast_FC():
    # 1. 設定基礎路徑
    base_dir = os.getcwd() # 根目錄
    
    # 來源資料夾 (讀取新資料): output_data_split/fc_filters
    src_dir = os.path.join(base_dir, 'output_data_split', 'fc_filters')
    
    # 目標資料夾 (要被附加的舊資料): output_data_packaged/tile17_ConvLast_FC
    dst_dir = os.path.join(base_dir, 'output_data_packaged', 'tile17_ConvLast_FC')

    # 2. 檢查目標資料夾是否存在
    if not os.path.exists(dst_dir):
        print(f"[Error] 目標資料夾不存在: {dst_dir}")
        print("請確認 tile17_ConvLast_FC 是否已經產生過基礎檔案。")
        return

    # 3. 定義具體的檔案對應任務 (來源檔名 -> 目標檔名)
    tasks = [
        ('Filter0.txt', 'Weight0.0.txt'),
        ('Filter1.txt', 'Weight0.1.txt'),
        ('Filter2.txt', 'Weight0.2.txt'),
        ('Filter3.txt', 'Weight0.3.txt'),
        ('Bias0.txt', 'Bias0.0.txt'),
        ('Bias1.txt', 'Bias0.1.txt'),
        ('Bias2.txt', 'Bias0.2.txt'),
        ('Bias3.txt', 'Bias0.3.txt')
    ]

    print(f"來源目錄: {src_dir}")
    print(f"目標目錄: {dst_dir}")
    print("-" * 30)

    # 準備用來存放生成的補零模板
    zero_templates = {}

    # 4. 執行檔案讀取與附加 (原始檔案) 並生成補零模板
    for src_file, dst_file in tasks:
        src_path = os.path.join(src_dir, src_file)
        dst_path = os.path.join(dst_dir, dst_file)
        
        try:
            if os.path.exists(src_path) and os.path.exists(dst_path):
                
                # A. 讀取來源資料
                with open(src_path, 'r', encoding='utf-8') as f_src:
                    lines = f_src.readlines()
                    new_content = "".join(lines)
                    
                    # 計算來源檔案有多少非空白行，以此作為補零模板的行數
                    valid_lines_count = len([line for line in lines if line.strip()])

                # B. 附加到目標檔案
                with open(dst_path, 'a', encoding='utf-8') as f_dst:
                    f_dst.write('\n\n') # 依照需求加入分隔符號
                    f_dst.write(new_content) # 寫入新內容

                print(f"[Success] 已將 {src_file} 附加至 {dst_file}")
                
                # C. 生成並儲存補零模板
                # 從檔名中萃取出編號 (例如 Filter0 -> 0)
                if 'Filter' in src_file:
                    idx = src_file.replace('Filter', '').replace('.txt', '')
                    template_str = '\n'.join(['00 00 00 00'] * valid_lines_count)
                    zero_templates[f'Weight_{idx}'] = template_str
                elif 'Bias' in src_file:
                    idx = src_file.replace('Bias', '').replace('.txt', '')
                    template_str = '\n'.join(['0000'] * valid_lines_count)
                    zero_templates[f'Bias_{idx}'] = template_str

            else:
                if not os.path.exists(src_path):
                    print(f"[Warning] 找不到來源檔案: {src_file}")
                if not os.path.exists(dst_path):
                    print(f"[Warning] 找不到目標檔案 (無法附加): {dst_file}")

        except Exception as e:
            print(f"[Error] 處理 {src_file} -> {dst_file} 時發生錯誤: {e}")

    print("-" * 30)
    print("開始處理補零檔案...")
    
    # 5. 處理指定的補零檔案
    # 使用迴圈自動產生需要補零的檔案清單 (Weight1.0~5.3, Bias1.0~5.3)
    pad_files_list = []
    for prefix in range(1, 6):
        for suffix in range(4):
            pad_files_list.append(f"Weight{prefix}.{suffix}.txt")
            pad_files_list.append(f"Bias{prefix}.{suffix}.txt")
            
    for pad_file in pad_files_list:
        pad_path = os.path.join(dst_dir, pad_file)
        
        # 決定該檔案要套用哪一個模板 (根據尾數 .0, .1, .2, .3 決定)
        try:
            if pad_file.startswith('Weight'):
                suffix = pad_file.split('.')[1]
                template_key = f'Weight_{suffix}'
            elif pad_file.startswith('Bias'):
                suffix = pad_file.split('.')[1]
                template_key = f'Bias_{suffix}'
            else:
                continue

            # 如果成功生成了對應的模板，就進行附加寫入
            if template_key in zero_templates:
                if os.path.exists(pad_path):
                    with open(pad_path, 'a', encoding='utf-8') as f_pad:
                        f_pad.write('\n\n')
                        f_pad.write(zero_templates[template_key])
                    print(f"[Success] 已將補零模板附加至 {pad_file}")
                else:
                    print(f"[Warning] 找不到補零目標檔案: {pad_file}")
            else:
                print(f"[Warning] 找不到對應的補零模板給檔案: {pad_file}")
                
        except Exception as e:
            print(f"[Error] 補零處理 {pad_file} 時發生錯誤: {e}")

    # 6. 執行終端機輸出
    display_path = os.path.join('output_data_packaged', 'tile17_ConvLast_FC').replace('/', '\\')
    
    print("-" * 30)
    print(f"已更新目錄：{display_path}")
    print("操作完成：output_data_split 的資料已附加在原始資料之後，且完成自動補零。")

if __name__ == '__main__':
    update_tile17_ConvLast_FC()