import os
from scraper_tenki import get_tenki_data

def main():
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    print("Bot starting...")
    print(f"Dry run mode: {dry_run}")

    tenki = get_tenki_data()
    print(f"Weather data: {tenki}")

if __name__ == "__main__":
    main()