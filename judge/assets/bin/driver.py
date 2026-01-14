import sys
import subprocess
import os

MAX_FILE_SIZE = 64 * 1024 * 1024

def main():
    argv = sys.argv[1:]
    if len(argv) < 3:
        sys.stderr.write("[Driver] Usage: driver.py <work_dir> <seed> <scale> [out_path_name]\n")
        sys.exit(1)

    work_dir = argv[0]
    seed = argv[1]
    scale = argv[2]
    case_in = argv[3]

    gen_path = os.path.join(work_dir, "gen.py")
    val_path = os.path.join(work_dir, "val.py")

    if not os.path.exists(gen_path):
        sys.stderr.write(f"[Driver] Error: gen.py not found at {gen_path}\n")
        sys.exit(1)

    # --- Step 1: 运行生成器 ---
    cmd_gen = [sys.executable, "gen.py", seed, scale]

    try:
        # ✅ 优化：使用 open 写入，方便未来扩展（如流式检查大小）
        with open(case_in, "wb") as f_out:
            process = subprocess.Popen(
                cmd_gen,
                stdout=f_out,
                stderr=sys.stderr,
                cwd=work_dir,
                env=os.environ
            )
            try:
                # 等待进程结束，设置超时防止死循环 (例如 15秒)
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                sys.stderr.write("\n[Driver] Generator Timeout (killed)\n")
                sys.exit(1)

            if process.returncode != 0:
                sys.stderr.write(f"\n[Driver] Generator Exit Code: {process.returncode}\n")
                sys.exit(process.returncode)

        # ✅ 优化：检查生成的文件大小
        if os.path.getsize(case_in) > MAX_FILE_SIZE:
            sys.stderr.write(f"\n[Driver] Error: Output file exceeded {MAX_FILE_SIZE / 1024 / 1024}MB limit.\n")
            os.remove(case_in)  # 删除超大文件
            sys.exit(1)

    except Exception as e:
        sys.stderr.write(f"\n[Driver] System Error: {e}\n")
        sys.exit(1)

    # --- Step 2: 运行校验器 (Validator) ---
    if os.path.exists(val_path):
        try:
            with open(case_in, "rb") as f_in:
                cmd_val = [sys.executable, "val.py"]
                subprocess.run(
                    cmd_val,
                    stdin=f_in,
                    stderr=sys.stderr,
                    check=True,
                    env=os.environ,
                    cwd=work_dir,
                    timeout=10
                )
        except subprocess.TimeoutExpired:
            sys.stderr.write(f"\n[Driver] Validator Timeout\n")
            sys.exit(1)

if __name__ == "__main__":
    main()