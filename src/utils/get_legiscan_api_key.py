import os

from dotenv import load_dotenv


def main():
    load_dotenv()

    try:
        LEGISCAN_API_KEY = os.environ["LEGISCAN_API_KEY"]
    except KeyError:
        print(
            "No Legiscan API key detected. You can get one at https://legiscan.com/user/register."
        )
        LEGISCAN_API_KEY = input("Enter LegiScan API key: ")
        print("\nWould you like to save this key for future use?")
        save_key = input("y/[n]: ") or "n"
        if save_key.lower() == "y":
            with open(".env", "a") as f:
                f.write(f"\nLEGISCAN_API_KEY={LEGISCAN_API_KEY}")
            print("API key saved to .env file")

    return LEGISCAN_API_KEY
