import subprocess


def run_startup_script():
    try:
        result = subprocess.run(
            ["./kafka-topics.sh"],
            check=True,
            capture_output=True,
            text=True
        )
        print("Startup script executed successfully:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Startup script failed:", e.stderr)