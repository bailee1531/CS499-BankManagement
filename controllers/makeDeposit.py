import subprocess

print(subprocess.run(["../scripts/customer/deposit.sh", 
                "arguments"], shell=True))