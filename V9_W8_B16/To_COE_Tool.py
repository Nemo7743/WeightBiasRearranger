# %% [markdown]
# # COE Tool
# 將指定資料夾內的 `.txt` 檔批次轉換為 Vivado BRAM 初始化用的 `.coe` 檔。
# 依檔名自動判斷：
# - 含 "Weight" -> 64-bit COE (原樣輸出)
# - 含 "Bias"   -> 64-bit COE (兩個32bit合併，高低位互換，奇數補0)
# 在 VSCode 互動式視窗 (Jupyter) 中，直接執行下方各個 Cell 即可。

# %%
import os

# ==========================================
# 核心轉換函式
# ==========================================

def clean_txt_to_coe_W(input_filename, output_filename=None):
    """
    讀取 txt，去除空白換行，將兩個 32-bit (8 chars) 合併為一個 64-bit (16 chars)。
    格式: Hex (Radix 16), 64-bit (16 hex chars) per line.
    邏輯：每兩行 (32-bit) 進行對調，即 Line2 + Line1。
    """
    if not os.path.exists(input_filename):
        print(f"錯誤：找不到檔案 '{input_filename}'")
        return

    if output_filename is None:
        base_name = os.path.splitext(input_filename)[0]
        output_filename = f"{base_name}.coe"

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            content = f.read()

        cleaned_content = content.replace(" ", "").replace("\n", "").replace("\r", "").upper()

        # 檢查是否為 8 的倍數 (32-bit boundary)
        if len(cleaned_content) % 8 != 0:
            print(f"[警告] {os.path.basename(input_filename)} 的資料長度不是 8 的倍數，解析可能會有偏差。")

        # 1. 先切分成 32-bit (8 chars) 的列表
        words_32b = [cleaned_content[i : i + 8] for i in range(0, len(cleaned_content), 8)]

        if not words_32b:
            print(f"[警告] 檔案 {input_filename} 內容為空。")
            return

        co_data_lines = []

        # 2. 每兩個一組進行對調合併 (Line2 + Line1)
        for i in range(0, len(words_32b), 2):
            low_word = words_32b[i]  # 原始順序的第 1 個 (放在低位/右邊)
            
            if i + 1 < len(words_32b):
                high_word = words_32b[i+1] # 原始順序的第 2 個 (放在高位/左邊)
                combined_64b = high_word + low_word
            else:
                # 奇數個情況：高位補 0
                combined_64b = "00000000" + low_word
            
            co_data_lines.append(combined_64b)

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write("memory_initialization_radix=16;\n")
            f.write("memory_initialization_vector=\n")

            for line in co_data_lines[:-1]:
                f.write(line + ",\n")

            f.write(co_data_lines[-1] + ";")

    except Exception as e:
        print(f"處理 {input_filename} 時發生錯誤：{e}")


def clean_txt_to_coe_B(input_filename, output_filename=None):
    """
    讀取 txt，去除空白換行，將四個 16-bit (4 chars) 合併為一個 64-bit (16 chars)。
    邏輯：
    1. 讀入所有 Hex 字串。
    2. 每四個 16-bit 一組。
    3. 順序調換：第4個在最高位，依序排到第1個在最低位 (右)。
    4. 若不足四個，則在高位補 16-bit 的 0。
    """
    if not os.path.exists(input_filename):
        print(f"錯誤：找不到檔案 '{input_filename}'")
        return

    if output_filename is None:
        base_name = os.path.splitext(input_filename)[0]
        output_filename = f"{base_name}.coe"

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # 清理字串
        cleaned_content = content.replace(" ", "").replace("\n", "").replace("\r", "").upper()

        # 檢查是否為 4 的倍數 (16-bit boundary)
        if len(cleaned_content) % 4 != 0:
            print(f"[警告] {os.path.basename(input_filename)} 的字元長度不是 4 的倍數，可能會導致解析錯誤。")

        # 1. 先切分成 16-bit (4 chars) 的列表
        words_16b = [cleaned_content[i : i + 4] for i in range(0, len(cleaned_content), 4)]

        if not words_16b:
            print(f"[警告] 檔案 {input_filename} 內容為空。")
            return

        co_data_lines = []

        # 2. 四個一組進行合併與調換
        for i in range(0, len(words_16b), 4):
            # 取出這一組（最多四個）
            group = words_16b[i : i + 4]
            
            # 補足四個 (在高位/左側補 0，但在 reversed 邏輯中，組內順序是 1,2,3,4 -> 4,3,2,1)
            # 如果只有兩個 [B1, B2]，補足後變成 [B1, B2, 0, 0]，反轉後變成 [0, 0, B2, B1]
            while len(group) < 4:
                group.append("0000")
            
            # 順序調換：[B1, B2, B3, B4] -> B4 + B3 + B2 + B1
            combined_64b = group[3] + group[2] + group[1] + group[0]
            
            co_data_lines.append(combined_64b)

        # 3. 寫入檔案
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write("memory_initialization_radix=16;\n")
            f.write("memory_initialization_vector=\n")

            for line in co_data_lines[:-1]:
                f.write(line + ",\n")

            # 最後一行加分號
            f.write(co_data_lines[-1] + ";")

    except Exception as e:
        print(f"處理 {input_filename} 時發生錯誤：{e}")



def process_folder_structure(source_root, target_root):
    """
    歷遍 source_root 資料夾，將所有 txt 檔轉換並輸出至 target_root，
    同時保持原有的資料夾結構。

    依照檔名自動判斷轉換模式：
        檔名含 'Weight' -> clean_txt_to_coe_W (64-bit COE)
        檔名含 'Bias'   -> clean_txt_to_coe_B (Merge 2x32b to 64b, Swapped)
        其餘檔案        -> 跳過並提示

    參數:
        source_root (str): 來源資料夾路徑
        target_root (str): 輸出目標資料夾路徑
    """
    print(f"開始處理資料夾：{source_root}")
    print(f"輸出目標資料夾：{target_root}")
    print("-" * 30)

    count = 0
    skipped = 0

    for dirpath, dirnames, filenames in os.walk(source_root):
        rel_path = os.path.relpath(dirpath, source_root)
        current_target_dir = os.path.join(target_root, rel_path)

        if not os.path.exists(current_target_dir):
            os.makedirs(current_target_dir)

        for filename in filenames:
            if not filename.lower().endswith('.txt'):
                continue

            src_file = os.path.join(dirpath, filename)
            base_name = os.path.splitext(filename)[0]
            dst_filename = base_name + ".coe"
            dst_file = os.path.join(current_target_dir, dst_filename)

            if 'Weight' in filename:
                clean_txt_to_coe_W(src_file, dst_file)
                tag = "[W 64-bit]"
                count += 1
                print(f"[OK] {tag} {rel_path}/{filename} -> {rel_path}/{dst_filename}")
            elif 'Bias' in filename:
                clean_txt_to_coe_B(src_file, dst_file)
                tag = "[B 64-bit]" # 標籤更新為 64-bit
                count += 1
                print(f"[OK] {tag} {rel_path}/{filename} -> {rel_path}/{dst_filename}")
            else:
                print(f"[跳過] {rel_path}/{filename}  (檔名不含 'Weight' 或 'Bias')")
                skipped += 1
                continue

    print("-" * 30)
    print(f"處理完成！共轉換了 {count} 個檔案，跳過 {skipped} 個檔案。")

print("✅ 函式載入完成！請執行下方對應的 Cell 開始轉換。")

# %% [markdown]
# ## ⚙️ 設定區
# **請修改下方 Cell 的路徑後執行即可。**
# - 路徑可使用**絕對路徑**（如 `r'C:\MyProject\Raw'`）或**相對路徑**（如 `'Raw'`）。
# - 相對路徑以 VSCode **開啟的工作區根目錄**為基準。
# - 程式依**檔名**自動判斷模式：含 `Weight` → 64-bit COE；含 `Bias` → 64-bit COE (Swap & Merge)。

# %%
# ==================== 路徑設定 ======================
input_folder  = r'output_data_packaged'    # <-- 修改來源資料夾
output_folder = r'output_data_packaged_COE'   # <-- 修改輸出資料夾

if os.path.exists(input_folder):
    process_folder_structure(input_folder, output_folder)
else:
    print(f"錯誤：找不到輸入資料夾 '{input_folder}'")