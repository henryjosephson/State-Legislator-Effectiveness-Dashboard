import os

from dotenv import load_dotenv


def main():
    load_dotenv()

    try:
        NY_SENATE_API_KEY = os.environ["NY_SENATE_API_KEY"]
    except KeyError:
        print(
            "No NY Senate API key detected. You can get one at https://legislation.nysenate.gov/public."
        )
        NY_SENATE_API_KEY = input("Enter LegiScan API key: ")
        print("\nWould you like to save this key for future use?")
        save_key = input("y/[n]: ") or "n"
        if save_key.lower() == "y":
            with open(".env", "a") as f:
                f.write(f"\nNY_SENATE_API_KEY={NY_SENATE_API_KEY}")
            print("API key saved to .env file")
    return NY_SENATE_API_KEY


if __name__ == "__main__":
    main()
