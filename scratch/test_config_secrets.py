import sys
import os

# Add the directory to path so we can import config
sys.path.append(os.getcwd())

try:
    import config
    print(f"SMTP Host: {config.SMTP_CONFIG.get('host')}")
    print(f"SMTP User: {config.SMTP_CONFIG.get('user')}")
    # Don't print the password, just check if it exists
    if config.SMTP_CONFIG.get('password'):
        print("Password found in config.")
    else:
        print("Password NOT found in config.")
except Exception as e:
    print(f"Error: {e}")
