import os

def truncate_file(input_path, output_path, is_weight):
    """
    Truncates hex strings in a file.
    Weights: 4 hex -> 2 hex (8-bit)
    Biases: 8 hex -> 8 hex (32-bit, keep original)
    """
    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line in f_in:
            if not line.strip():
                f_out.write(line)
                continue
            
            if is_weight:
                # Weights are space-separated 4-char hex strings
                truncated_parts = [part[-2:] for part in line.split()]
                f_out.write(" ".join(truncated_parts) + "\n")
            else:
                # Biases are line-separated 8-char hex strings
                # Keep all 8 characters for 32-bit bias
                truncated_val = line.strip()[-8:]
                f_out.write(truncated_val + "\n")

def run_truncation():
    input_dir = "data_model"
    output_dir = "data_model_8_32"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    files = os.listdir(input_dir)
    for filename in files:
        if filename.endswith(".txt") and filename != "0.資料排佈格式.txt":
            is_weight = filename.endswith("_w.txt")
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            # print(f"Processing {'Weight' if is_weight else 'Bias'}: {filename}")
            truncate_file(input_path, output_path, is_weight)
    
    # Copy the format description file as well
    import shutil
    shutil.copy(os.path.join(input_dir, "0.資料排佈格式.txt"), os.path.join(output_dir, "0.資料排佈格式.txt"))

    print("Truncation complete.")

if __name__ == "__main__":
    run_truncation()
