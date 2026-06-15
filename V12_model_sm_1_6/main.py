import os
import sys

# 引用組譯器
import a0_InstructionAssemblerV1 as InstructionAssembler
# 引用重排程式
import b0_WeightBiasRearranger_All as WeightBiasRearranger
# 引用打包程式
import c0_WeightBiasPackager as WeightBiasPackager

# --- Logger 類別 ---
class Logger(object):
    def __init__(self, filename="log.txt"):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # 為了相容性必須實作 flush
        self.terminal.flush()
        self.log.flush()

def main():
    # 將 stdout 重導向至 Logger
    sys.stdout = Logger("log.txt")

    # 組譯器檔案名稱設定
    instruction_file = 'data_instructions/InstructionSet.csv'
    input_file = 'data_instructions/instruction_input.txt'
    output_file = 'data_instructions/instruction_output.txt'
    
    print("--- [Step 0] 開始組合語言組譯流程 ---")
    InstructionAssembler.InstructionAssembler(instruction_file, input_file, output_file)
    print("--- [Step 0] 結束組合語言組譯流程 ---")

    print("\n")
    print("--- [Step 1] 開始權重與資料切分流程 ---")
    WeightBiasRearranger.run_weight_rearrange()
    print("--- [Step 1] 結束權重與資料切分流程 ---")

    print("\n")
    print("--- [Step 2] 開始權重與資料打包流程 ---")
    WeightBiasPackager.run_weight_Packager()
    print("--- [Step 2] 結束權重與資料打包流程 ---")

if __name__ == "__main__":
    main()