# WeightBiasRearranger 使用說明

本工具用於對神經網路模型（ShuffleNetV2）的權重與偏置資料進行重排、打包，並產生 Vivado BRAM 初始化用的 `.coe` 檔。

---

## 版本說明

| 版本 | 資料夾 | Weight 精度 | Bias 精度 | 說明 |
|------|--------|------------|----------|------|
| V8   | `V8/`              | 8-bit (原始) | 32-bit (原始) | 穩定版，直接使用 `data_model` 原始資料 |
| V9   | `V9_W8_B16/`       | 8-bit        | 16-bit        | 在 V8 基礎上對 Bias 截短為 16-bit |
| V10  | `V10_W8_B32/`      | 8-bit        | 32-bit        | 在 V8 基礎上重新整理 Bias，保留完整 32-bit |
| V12  | `V12_model_sm_1_6/` | 8-bit       | 32-bit        | 使用 ShuffleNet sm1.6 新版模型，指令集 `change buffer sel` 擴展為 6-bit |

---

## V12（model\_sm\_1\_6，最新版）

### 與 V8 的主要差異

| 項目 | V8 | V12 |
|------|----|-----|
| 模型資料 | 原始 ShuffleNetV2 | ShuffleNet sm1.6（約 59 個 weight/bias 檔案不同） |
| `change buffer sel` 欄位 | 4-bit（例：`1111`） | 6-bit（例：`110101`） |
| 指令集 Excel | `IS_260301.xlsx` | `IS_260403_devan_Backup_2.xlsx` |
| 額外輸出工具 | 無 | `COE_To_Bin.ipynb`（COE → Binary 轉換） |

### 資料夾結構

```
V12_model_sm_1_6/
├── main.py                        # 主程式入口
├── a0_InstructionAssemblerV1.py   # Step 0：組合語言組譯器
├── b0_WeightBiasRearranger_All.py # Step 1：權重重排（總入口）
├── b1~b5_*.py                     # Step 1：各層重排子程式
├── c0_WeightBiasPackager.py       # Step 2：權重打包（總入口）
├── c1~c6_*.py                     # Step 2：各 Tile 打包子程式
├── T_COE_Tool.py                  # 輔助工具：txt → .coe 轉換
├── COE_To_Bin.ipynb               # 輔助工具：.coe → Binary 轉換（V12 新增）
├── Calculate_Output_Folder.py     # 輔助工具：輸出資料夾統計
├── sm1.6_all_layers_weight_bias_64b.txt  # 所有層彙整的 64-bit 權重/偏置（V12 新增）
├── sm1.6_layers_weight_bias_64b.bin      # 上述的 Binary 輸出（V12 新增）
├── data_instructions/             # 指令集相關檔案
│   ├── Top_IS/
│   │   ├── IS_260403_devan_Backup_2.xlsx  # 最新指令集 Excel（目前使用版本）
│   │   ├── IS_260403_devan.xlsx           # Devan 修改版本
│   │   ├── IS_260403_devan_Backup_0.xlsx  # 備份 0
│   │   ├── IS_260403_devan_Backup_1.xlsx  # 備份 1
│   │   ├── IS_260301_stabel_backup.xlsx   # V8 穩定版備份
│   │   └── to_COE.py                      # Excel → .coe 轉換腳本
│   ├── InstructionSet.csv
│   ├── instruction_input.txt
│   └── instruction_output.txt
├── data_model/                    # sm1.6 模型權重與偏置（hex 格式 txt）
├── output_data_split/             # Step 1 輸出：重排後的資料
└── output_data_packaged/          # Step 2 輸出：打包後的資料
```

### 執行步驟

**前置條件：** 確認 `data_model/` 下已放好所有層的 `*_w.txt` 與 `*_b.txt`，以及 `data_instructions/instruction_input.txt` 已填寫好組合語言指令。

**Step 0 ~ 2：執行主程式**

```bash
cd V12_model_sm_1_6
python main.py
```

執行後會依序完成：
- **Step 0**：組合語言組譯 → 輸出至 `data_instructions/instruction_output.txt`
- **Step 1**：權重與偏置重排 → 輸出至 `output_data_split/`
- **Step 2**：資料打包成 Tile 格式 → 輸出至 `output_data_packaged/`

執行日誌會同步寫入 `log.txt`。

**Step 3（選用）：轉換為 .coe 檔**

在 VSCode 互動式視窗（Jupyter 模式）中開啟 `T_COE_Tool.py`，確認路徑設定後執行：

```python
input_folder  = r'output_data_packaged'    # 來源資料夾
output_folder = r'output_data_packaged_COE'  # 輸出資料夾
```

依檔名自動判斷轉換模式：
- 檔名含 `Weight` → 64-bit COE（原樣合併）
- 檔名含 `Bias`   → 64-bit COE（每兩個 32-bit 合併，高低位互換）

**Step 3.5（選用）：將 .coe 轉換為 Binary**

開啟 `COE_To_Bin.ipynb` 並執行，將 COE 格式輸出轉為 `.bin` 二進制檔案。

**Step 4（選用）：更新指令集 .coe 檔**

指令集 Excel 檔位於 `data_instructions/Top_IS/`，目前使用版本為：

```
data_instructions/Top_IS/IS_260403_devan_Backup_2.xlsx
```

> **注意：** 若需修改指令集，請編輯上述 Excel 後執行同資料夾下的 `to_COE.py` 重新產生 `IS.coe`。
> 執行前請確認刪除 Excel 中的粉紅色儲存格，否則會導致轉換錯誤。

**Step 5（選用）：查看輸出資料夾統計**

```bash
python Calculate_Output_Folder.py
```

輸出各 Tile 資料夾大小與每個檔案的資料筆數、預計傳輸次數。

---

## V9（W8\_B16）

### 與 V8 的差異

V9 在執行主程式前，需先對 `data_model/` 中的原始資料進行**截短（Truncation）**：
- **Weight**：4-char hex → 2-char hex（保留低 8-bit）
- **Bias**：8-char hex → 4-char hex（保留低 16-bit）

截短後的資料存放於 `data_model_8_16/`，後續所有步驟使用此資料夾。

### 資料夾結構

```
V9_W8_B16/
├── main.py
├── truncate_weights_bias.py   # 截短工具（需先執行）
├── verify_truncation.py       # 驗證截短結果是否正確
├── To_COE_Tool.py             # 輔助工具：txt → .coe 轉換（B 為 16-bit 版）
├── Calculate_Output_Folder.py
├── data_model/                # 原始模型資料（不修改）
├── data_model_8_16/           # 截短後的資料（由 truncate_weights_bias.py 產生）
├── output_data_split/
└── output_data_packaged/
```

### 執行步驟

**Step 前置：截短資料**

```bash
cd V9_W8_B16
python truncate_weights_bias.py
```

執行後在 `data_model_8_16/` 產生截短後的 txt 檔。

**（選用）驗證截短結果**

```bash
python verify_truncation.py
```

輸出 `[PASS]` / `[FAIL]` 確認 Weight 為 2-char、Bias 為 4-char。

**Step 0 ~ 2：執行主程式**

```bash
python main.py
```

流程與 V8 相同（組譯 → 重排 → 打包），但內部讀取的模型資料來自 `data_model_8_16/`。

**Step 3（選用）：轉換為 .coe 檔**

在 VSCode 互動式視窗中開啟 `To_COE_Tool.py` 並執行。

與 V8 的差異：Bias 的 COE 轉換邏輯改為**四個 16-bit 合併為一個 64-bit**（順序反轉：B4+B3+B2+B1）。

---

## V10（W8\_B32）

### 與 V8 的差異

V10 同樣在執行主程式前需先執行截短，但 Bias **保留完整 32-bit（8-char hex）**，只有 Weight 截短。

- **Weight**：4-char hex → 2-char hex（保留低 8-bit）
- **Bias**：8-char hex → 8-char hex（不截短，原樣保留）

截短後的資料存放於 `data_model_8_32/`。

### 資料夾結構

```
V10_W8_B32/
├── main.py
├── truncate_weights_bias.py   # 截短工具（需先執行）
├── verify_truncation.py       # 驗證截短結果
├── To_COE_Tool.py             # 輔助工具：txt → .coe 轉換（B 為 32-bit 版）
├── Calculate_Output_Folder.py
├── data_model/                # 原始模型資料（不修改）
├── data_model_8_32/           # 截短後的資料（由 truncate_weights_bias.py 產生）
├── output_data_split/
└── output_data_packaged/
```

### 執行步驟

**Step 前置：截短資料**

```bash
cd V10_W8_B32
python truncate_weights_bias.py
```

執行後在 `data_model_8_32/` 產生處理後的 txt 檔（Weight 截短，Bias 原樣）。

**（選用）驗證截短結果**

```bash
python verify_truncation.py
```

**Step 0 ~ 2：執行主程式**

```bash
python main.py
```

流程與 V8 相同，模型資料來自 `data_model_8_32/`。

**Step 3（選用）：轉換為 .coe 檔**

在 VSCode 互動式視窗中開啟 `To_COE_Tool.py` 並執行。

Bias 的 COE 轉換邏輯為**兩個 32-bit 合併為一個 64-bit**（高低位互換：B2+B1）。

---

## 指令集說明

以下是自定義指令集的指令內容：

<img width="728" height="656" alt="image" src="https://github.com/user-attachments/assets/e39c3384-502c-4e7f-be77-d25dae190832" />

### 使用範例

```
Change_data_flow.conv1
Change_parameter.fmap 1111 2222
get_dram_data.fmap 0001 0002 2567
get_dram_data.fmap 0001 0002 0003
tile_control.load_cal_out 2877 5678
```

### 輸出範例

```
0000
1002 1111 2222
2013 0001 0002 2567
2013 0001 0002 0003
4242 2877 5678
```
