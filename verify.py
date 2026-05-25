import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from terminal_ui.qvoid_shell import QVoidShell

def run_tests():
    print("--- STARTING Q-VOID VERIFICATION ---")
    shell = QVoidShell()
    
    commands = [
        "status",
        "encrypt secretdata",
        "decrypt",
        "ghost list",
        "trap status",
        "hive status",
        "precog nmap 22",
        "polymorph status",
        "forge list",
        "oracle status",
        "mcp analyze payload",
        "rag threat",
        "dna encode hidden",
        "qpm list",
        "audit"
    ]
    
    for cmd in commands:
        print(f"\n>> EXECUTING: {cmd}")
        try:
            shell._dispatch(cmd)
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    run_tests()
