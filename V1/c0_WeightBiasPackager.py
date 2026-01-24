import os

# 引用各打包程式
import c1_WeightBiasPackager_Tile0_Conv1V2 as tile0
import c2_WeightBiasPackager_Tile_DownSampling_LV2 as Tile_DownSampling_L
import c3_WeightBiasPackager_Tile_DownSampling_RV2 as Tile_DownSampling_R
import c4_WeightBiasPackager_Tile_OGShuffleV2 as Tile_OGShuffle
import c5_WeightBiasPackager_Tile17_ConvLastV2 as Tile_ConvLast
import c6_WeightBiasPackager_Tile18_FCV1 as Tile_FC

def run_weight_Packager():
    # --- 執行 Tile0 (Conv1) ---
    print("--- 打包 Tile0 ---")
    tile0.package_tile0_Conv1()
    print("--- 打包 Tile0 結束 ---")

    # --- 執行 Tile1 (DownSampling) ---
    print("--- 打包 Tile1 ---")
    Tile_DownSampling_L.package_tile_downSampling_L(0)
    Tile_DownSampling_R.package_tile_downSampling_R(0)
    print("--- 打包 Tile1 結束 ---")

    # --- 執行 Tile2 到 Tile4 (OGshuffle) ---
    for i in range(1, 4):
        print(f"--- 打包 Tile{1+i} ---")
        Tile_OGShuffle.package_tile_OGshuffle(i)
        print(f"--- 打包 Tile{1+i} 結束 ---")

    # --- 執行 Tile5 (DownSampling) ---
    print("--- 打包 Tile5 ---")
    Tile_DownSampling_L.package_tile_downSampling_L(4)
    Tile_DownSampling_R.package_tile_downSampling_R(4)
    print("--- 打包 Tile5 結束 ---")

    # --- 執行 Tile6 到 Tile12 (OGshuffle) ---
    for i in range(5, 12):
        print(f"--- 打包 Tile{1+i} ---")
        Tile_OGShuffle.package_tile_OGshuffle(i)
        print(f"--- 打包 Tile{1+i} 結束 ---")
    
    # --- 執行 Tile13 (DownSampling) ---
    print("--- 打包 Tile13 ---")
    Tile_DownSampling_L.package_tile_downSampling_L(12)
    Tile_DownSampling_R.package_tile_downSampling_R(12)
    print("--- 打包 Tile13 結束 ---")

    # --- 執行 Tile14 到 Tile16 (OGshuffle) ---
    for i in range(13, 16):
        print(f"--- 打包 Tile{1+i} ---")
        Tile_OGShuffle.package_tile_OGshuffle(i)
        print(f"--- 打包 Tile{1+i} 結束 ---")
    
    # --- 執行 Tile17 (ConvLast) ---
    print("--- 打包 Tile17 ---")
    Tile_ConvLast.package_tile17_convlast()
    print("--- 打包 Tile17 結束 ---")

    # --- 執行 Tile18 (FC) ---
    print("--- 打包 Tile18 ---")
    Tile_FC.package_tile18_FC()
    print("--- 打包 Tile18 結束 ---")

# --- 執行 Function ---
if __name__ == "__main__":
    run_weight_Packager()