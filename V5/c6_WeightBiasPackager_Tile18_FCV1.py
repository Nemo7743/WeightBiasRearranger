import os
import shutil


def package_tile18_FC():
    # 1. 設定基礎路徑
    # 使用 os.path.join 確保跨平台兼容性 (Windows/Linux)
    base_dir = os.getcwd() # 根目錄

   
    # 來源資料夾: output_data_split/fc_filters
    src_dir = os.path.join(base_dir, 'output_data_split', 'fc_filters')

   
    # 目標資料夾: output_data_packaged/tile18
    dst_dir = os.path.join(base_dir, 'output_data_packaged', 'tile18_FC')



    # 2. 確保目標資料夾存在，不存在則建立
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    # 3. 定義具體的檔案操作任務 (來源檔名 -> 目標檔名)
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


    # 4. 執行檔案複製與改名
    for src_file, dst_file in tasks:
        src_path = os.path.join(src_dir, src_file)
        dst_path = os.path.join(dst_dir, dst_file)

        try:
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path) # 使用 copy2 複製檔案並保留屬性
            else:
                print(f"[Warning] 找不到來源檔案: {src_path}")
        except Exception as e:
            print(f"[Error] 處理 {src_file} 時發生錯誤: {e}")


    # 5. 執行終端機輸出 (依照指定格式)
    # 為了顯示出 output_data_packaged\tile1.1 (或 tile18) 的 Windows 風格路徑
    display_path = os.path.join('output_data_packaged', 'tile18_FC').replace('/', '\\')

   
    print(f"已確認輸出目錄：{display_path}")
    print("正在將 4 個過濾器分散處理為 4 組...")
    print(f"  已生成 Weight0.0.txt   包含 Filter: [0]")
    print(f"  已生成 Weight0.1.txt   包含 Filter: [1]")
    print(f"  已生成 Weight0.2.txt   包含 Filter: [2]")
    print(f"  已生成 Weight0.3.txt   包含 Filter: [3]")
    print(f"  已生成 Bias0.0.txt   包含 Bias: [0]")
    print(f"  已生成 Bias0.1.txt   包含 Bias: [1]")
    print(f"  已生成 Bias0.2.txt   包含 Bias: [2]")
    print(f"  已生成 Bias0.3.txt   包含 Bias: [3]")
    print("打包完成。")



if __name__ == '__main__':
    package_tile18_FC()