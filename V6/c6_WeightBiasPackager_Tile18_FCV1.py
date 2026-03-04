import os

def update_tile17_ConvLast_FC():
    # 1. 設定基礎路徑
    base_dir = os.getcwd() # 根目錄
    
    # 來源資料夾 (讀取新資料): output_data_split/fc_filters
    src_dir = os.path.join(base_dir, 'output_data_split', 'fc_filters')
    
    # 目標資料夾 (要被附加的舊資料): output_data_packaged/tile17_ConvLast_FC
    dst_dir = os.path.join(base_dir, 'output_data_packaged', 'tile17_ConvLast_FC')

    # 2. 檢查目標資料夾是否存在
    # 因為是要附加在現有檔案後面，如果資料夾不存在，通常代表流程有誤，這裡做個檢查
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

    # 4. 執行檔案讀取與附加
    for src_file, dst_file in tasks:
        src_path = os.path.join(src_dir, src_file)
        dst_path = os.path.join(dst_dir, dst_file)
        
        try:
            # 確保來源檔案與目標檔案都存在
            if os.path.exists(src_path) and os.path.exists(dst_path):
                
                # A. 讀取來源資料 (output_data_split 裡的資料)
                with open(src_path, 'r', encoding='utf-8') as f_src:
                    new_content = f_src.read()

                # B. 附加到目標檔案 (tile17 裡的資料)
                # 使用 'a' (append) 模式開啟目標檔案
                with open(dst_path, 'a', encoding='utf-8') as f_dst:
                    f_dst.write('\n\n') # 依照需求加入分隔符號
                    f_dst.write(new_content) # 寫入新內容

                print(f"[Success] 已將 {src_file} 附加至 {dst_file}")

            else:
                if not os.path.exists(src_path):
                    print(f"[Warning] 找不到來源檔案: {src_file}")
                if not os.path.exists(dst_path):
                    print(f"[Warning] 找不到目標檔案 (無法附加): {dst_file}")

        except Exception as e:
            print(f"[Error] 處理 {src_file} -> {dst_file} 時發生錯誤: {e}")

    # 5. 執行終端機輸出
    display_path = os.path.join('output_data_packaged', 'tile17_ConvLast_FC').replace('/', '\\')
    
    print("-" * 30)
    print(f"已更新目錄：{display_path}")
    print("操作完成：output_data_split 的資料已附加在 tile17 原始資料之後。")

if __name__ == '__main__':
    update_tile17_ConvLast_FC()