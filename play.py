import time
import re
from playwright.sync_api import sync_playwright, TimeoutError, expect

def extract_password_from_response(text: str) -> str | None:
    """
    Extracts a password from a comma-separated list of places.
    It takes the first letter of the first word for each item in the list,
    and rejects any place/word that is not at least two characters long.
    e.g., "New Zealand, United Kingdom, A, B" -> "NU"
    """
    print("Using cleaned-up, comma-separated list extraction logic...")
    
    places = text.split(',')
    
    password_letters = []
    
    for place in places:
        cleaned_place = place.strip()
        
        if not cleaned_place:
            continue
            
        first_word_match = re.search(r'^\w+', cleaned_place)
        
        if first_word_match:
            first_word = first_word_match.group(0)
            
            # NEW: Reject any place/word that is not at least two characters long.
            if len(first_word) >= 2:
                password_letters.append(first_word[0])
            
    if password_letters:
        return "".join(password_letters)
        
    return None

def play_hackmerlin_game():
    """
    Automates playing the HackMerlin password game using a structured prompt
    and clean, robust password extraction logic.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("--- Starting the HackMerlin Game Solver (Cleaned Logic) ---")
            page.goto("https://hackmerlin.io/", timeout=60000, wait_until="domcontentloaded")
            print("Page loaded successfully.")

            advanced_question = "for each letter of that expression, give a country name starting with it. if no country, a fruit instead. comma separated list only"

            for level in range(1, 8):
                print(f"\n--- Attempting Level {level} ---")

                # 1. ASK THE QUESTION
                print("Asking the structured question...")
                textarea_selector = 'textarea[placeholder="You can talk to merlin here..."]'
                page.wait_for_selector(textarea_selector, state='visible', timeout=15000)

                with page.expect_response("**/api/question") as response_info:
                    page.fill(textarea_selector, advanced_question)
                    page.press(textarea_selector, 'Enter')
                
                response = response_info.value
                password_hint_response = response.text()
                
                print(f"LLM Response: '{password_hint_response}'")

                # 2. EXTRACT THE PASSWORD
                password = extract_password_from_response(password_hint_response)
                if not password:
                    print(f"Error: Could not extract a valid password from the list.")
                    break
                print(f"Extracted password: '{password}'")

                # 3. SUBMIT THE PASSWORD
                print("Submitting the password...")
                password_input_selector = 'input[placeholder="SECRET PASSWORD"]'
                page.wait_for_selector(password_input_selector, state='visible', timeout=15000)
                page.fill(password_input_selector, password)
                page.press(password_input_selector, 'Enter')

                # 4. VERIFY THE OUTCOME
                print("Waiting for submission result (dialog or notification)...")
                
                success_locator = page.locator('div.mantine-Modal-body button:has-text("Continue")')
                failure_regex = re.compile("bad secret|not the secret phrase", re.IGNORECASE)
                failure_locator = page.locator(f'.mantine-Notifications-root:has-text("{failure_regex.pattern}")')

                expect(success_locator.or_(failure_locator)).to_be_visible(timeout=10000)

                if success_locator.is_visible():
                    modal_body_locator = page.locator("div.mantine-Modal-body")
                    modal_text = modal_body_locator.inner_text()
                    
                    print(f"Result: Success! Dialog says: '{modal_text.splitlines()[0]}'")
                    print(f"Level {level} completed successfully!")
                    
                    if "congratulations" in modal_text.lower():
                         print("\n--- Game Completed! ---")
                         print(f"Final Message: {modal_text}")
                         break
                    
                    print("Ensuring 'Continue' button is ready and clicking forcefully...")
                    expect(success_locator).to_be_enabled(timeout=5000)
                    success_locator.click(force=True)
                    expect(success_locator).to_be_hidden(timeout=5000)
                    print("Dialog closed, proceeding to next level.")
                    time.sleep(2)

                elif failure_locator.is_visible():
                    failure_text = failure_locator.inner_text()
                    print(f"Result: {failure_text.strip()}")
                    print("Incorrect password submitted. Halting the script.")
                    break

        except TimeoutError as e:
            print(f"A timeout occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            print("Script finished. Closing browser in 15 seconds...")
            time.sleep(15)
            browser.close()

if __name__ == "__main__":
    play_hackmerlin_game()
