import os

# 引用外部重排程式
import b1_WeightBiasRearranger_Conv1V2 as conv1
import b2_WeightBiasRearranger_DepthWiseV1 as dw
import b3_WeightBiasRearranger_PointWiseV1 as pw
import b4_WeightBiasRearranger_ConvLastV1 as conv_last
import b5_WeightBiasRearranger_FCV1 as fc

def run_weight_rearrange():

    # --- 執行 Conv1 (b 檔案) ---
    conv1.run_all()

    # --- 執行 DepthWise (c 檔案) ---
    dw.run_all()

    # --- 執行 PointWise (d 檔案) ---
    pw.run_all()

    # --- 執行 ConvLast (e 檔案) ---
    conv_last.run_all()

    # --- 執行 FC (f 檔案) ---
    fc.run_all()

if __name__ == "__main__":
    run_weight_rearrange()