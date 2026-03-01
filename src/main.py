import os

def main():
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    print("Bot starting...")
    print(f"Dry run mode: {dry_run}")
    print("SUCCESS: main.py executed correctly")

if __name__ == "__main__":
    main()