import os
import re
import math

# 設定目標資料夾名稱
base_dir = "output_data_packaged"

def natural_sort_key(s):
    """
    用於自然排序的 key function (讓 tile1.2 在 tile1.10 之前)
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def get_folder_size_str(folder_path):
    """
    計算資料夾大小並回傳格式化字串 (如 4.66 KB)
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    
    if total_size < 1024:
        return f"({total_size} B)"
    elif total_size < 1024 * 1024:
        return f"({total_size / 1024:.2f} KB)"
    else:
        return f"({total_size / (1024 * 1024):.2f} MB)"

def count_numbers_in_file(filepath):
    """
    計算檔案內的數字個數 (以空白或換行分隔)
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # 使用 split() 自動處理所有空白字元 (空格、換行、Tab)
            numbers = content.split()
            return len(numbers)
    except Exception as e:
        return f"Error: {e}"

def main():
    if not os.path.exists(base_dir):
        print(f"找不到資料夾: {base_dir}")
        print("請確認此 python 檔是否與 output_data_packaged 在同一層目錄。")
        return

    # 取得所有子資料夾並排序
    folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    folders.sort(key=natural_sort_key)

    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        size_str = get_folder_size_str(folder_path)
        
        # 輸出資料夾名稱與大小
        print(f"{folder}\t{size_str}")

        # 取得該資料夾下的所有 txt 檔案並排序
        files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
        files.sort(key=natural_sort_key)

        for filename in files:
            filepath = os.path.join(folder_path, filename)
            count = count_numbers_in_file(filepath)
            
            # 依照格式輸出：檔名 與 數字個數
            if(filename[0] == "B"):
                print(f"\t{filename} : {count} 個數字   傳輸 {math.ceil(count/4)} 次")
            elif(filename[0] == "W"):
                print(f"\t{filename} : {count} 個數字   傳輸 {math.ceil(count/8)} 次")
            else:
                print("這是哪？!!!!!!!")
            
        
        # 每個資料夾處理完後空一行，方便閱讀
        print()

if __name__ == "__main__":
    main()