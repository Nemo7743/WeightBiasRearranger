import os

# 引用組譯器
import a0_InstructionAssemblerV1 as InstructionAssembler
# 引用外部重排程式
import b0_WeightBiasRearranger_All as WeightBiasRearranger


def main():
    # 組譯器檔案名稱設定
    instruction_file = 'data_instructions/InstructionSet.csv'
    input_file = 'data_instructions/instruction_input.txt'
    output_file = 'data_instructions/instruction_output.txt'
    InstructionAssembler.InstructionAssembler(instruction_file, input_file, output_file)

    print("\n")
    print("--- [Step 1] 開始權重與資料切分流程 ---")
    WeightBiasRearranger.run_weight_rearrange()
    print("--- [Step 1] 所有資料切分完成 ---\n")


if __name__ == "__main__":
    main()