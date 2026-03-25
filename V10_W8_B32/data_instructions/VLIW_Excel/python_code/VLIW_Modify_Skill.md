# VLIW Modify Skill

本文件記錄了關於 VLIW Excel 檔案結構的分析結果與 Python 腳本修改技巧，用以日後自動化修改指令。目前已更新至支援跨檔案樣式參考與條件式標籤修改邏輯。

## 1. VLIW Excel 檔案結構分析

根據對 `UnitX_Y_xxx.xlsx` 系列檔案的檢查，發現所有 VLIW 檔案都有非常嚴謹且一致的排列結構：

* **標題列區域 (Header Rows):**
  - 第 1 列 (Row 1): `OP_Code` 及其參數標題 (如 `core_en [6]`, `NoC_en [3]`)
  - 第 2 列 (Row 2): `Core` 及其參數標題
  - 第 3 列 (Row 3): `TBO` 及其參數標題
  - 第 4 列 (Row 4): `NoC` 及其參數標題
  - 第 5 列 (Row 5): `PreP` 及其參數標題 (如 `Requant_Sel[3]`)

* **空白列 (Blank Row):**
  - 第 6 列 (Row 6): 通常為完全空白的一列 (`None`)，無實質數據。

* **資料列區域 (Data Rows):**
  每一條 VLIW 剛好包含 **5 列** 的 Excel 儲存格，順序如下：
  - (區塊的第 1 列) Row 7, 12, 17... : `OP_Code` 指令 (Column C 通常包含功能的文字標籤，如 `input`, `conv1`)
  - (區塊的第 2 列) Row 8, 13, 18... : `Core` 指令
  - (區塊的第 3 列) Row 9, 14, 19... : `TBO` 指令
  - (區塊的第 4 列) Row 10, 15, 20... : `NoC` 指令
  - (區塊的第 5 列) Row 11, 16, 21... : `PreP` 指令 (目標參數 `Requant_Sel[3]` 位於此列)

## 2. 修改腳本的關鍵技巧

### (1) 定位正確的填寫列數 (Row Offset)
當我們想針對特定指令類別（如 `PreP` 層級）修改參數時，必須考量區塊內的相對位移：
- **靜態對齊**：若已知全部都要修改，可使用 `range(start_row, max_row + 1, 5)`，其中 `start_row` 需設為標題列後的第 5 列 (如 Row 11)。
- **動態對齊 (基於 OP_Code)**：若是以掃描 `OP_Code` 標籤為基準，當在第 `r` 列發現目標標籤時，其對應的 `PreP` 參數列位於 **`r + 4`**。

### (2) 避免 Excel 通用格式自動轉型
寫入位元字串（例如 `"000"`, `"100"`）時，必須強制設定儲存格格式，否則 Excel 會將 `000` 轉為數字 `0`。
```python
cell.number_format = '@'  # 強制設定為文字格式
cell.value = '100'        # 寫入字串
```

### (3) 跨檔案樣式與顏色參考 (Cell Styling)
為了維持視覺美觀與一致性，建議使用一個「基準檔案」作為樣式模板。
```python
from copy import copy
# 從 Unit0_1_PreP.xlsx 讀取 Requant_Sel[3] 標題的底色
ref_fill = copy(ws_ref.cell(row=header_row, column=target_col).fill)
# 套用到目標檔案的修改儲存格
cell.fill = ref_fill
```

### (4) 基於標籤的條件分支邏輯 (Conditional Branching)
在處理複雜任務（如 `Unit0_2`）時，`Requant_Sel[3]` 的值需視 `OP_Code` 的類型而定。腳本會根據 Column C 的關鍵字進行判斷：
- **`input`**, **`max`**, **`output`** -> 填入 **`000`**
- **`conv1`** -> 填入 **`100`**

## 3. 自動化修改 S.O.P

1. **載入參考樣式**：從基準檔案（如 `Unit0_1`）獲取目標欄位的背景顏色。
2. **定位目標欄位**：動態尋找 `Requant_Sel[3]` 所在列編號 (Column Index)。
3. **掃描資料塊**：遍歷工作表，尋找 `OP_Code` 列中的文字標記。
4. **定位並修改**：根據標記類型，跳轉至對應的 `PreP` 列 (`r + 4`) 修改值與格式。
5. **儲存檔案**：確認寫入成功並保留原始 Excel 排版樣式。


