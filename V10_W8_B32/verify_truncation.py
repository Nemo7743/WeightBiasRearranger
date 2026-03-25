import os

def verify():
    input_dir = "data_model"
    output_dir = "data_model_8_32"
    
    if not os.path.exists(output_dir):
        print(f"[FAIL] Output directory {output_dir} does not exist.")
        return

    input_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    output_files = [f for f in os.listdir(output_dir) if f.endswith(".txt")]

    if len(input_files) != len(output_files):
        print(f"[FAIL] File count mismatch: {len(input_files)} vs {len(output_files)}")
    else:
        print(f"[PASS] File count matches: {len(input_files)}")

    # Sample verification
    sample_w = "conv1.0_w.txt"
    sample_b = "conv1.0_b.txt"

    if sample_w in output_files:
        with open(os.path.join(output_dir, sample_w), 'r') as f:
            first_line = f.readline().strip().split()
            if all(len(word) == 2 for word in first_line):
                print(f"[PASS] {sample_w} truncated correctly (8-bit/2-char).")
            else:
                print(f"[FAIL] {sample_w} truncation failed. Lengths: {[len(w) for w in first_line[:5]]}")

    if sample_b in output_files:
        with open(os.path.join(output_dir, sample_b), 'r') as f:
            first_val = f.readline().strip()
            if len(first_val) == 8:
                print(f"[PASS] {sample_b} kept correctly (32-bit/8-char).")
            else:
                print(f"[FAIL] {sample_b} verification failed. Length: {len(first_val)}")

if __name__ == "__main__":
    verify()
