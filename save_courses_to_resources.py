import csv
import time
import os
import builtins
from pathlib import Path
from playwright.sync_api import sync_playwright

def custom_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    builtins.print(*args, **kwargs)
    with open("Logs.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

print = custom_print

# ==========================================
# CONFIGURATION
# ==========================================
# Mode 1: Save to Resources and Export (no download)
# Mode 2: Download exported files from Transfer History
MODE = 2

# Directory to save downloaded files (Mode 2)
# Defaults to system Downloads folder
# /Volumes/Schoology-Backup-1/100-Benchmark
# DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
DOWNLOAD_DIR = os.path.expanduser("/Volumes/Schoology-Backup-1/23-24")

# School Year for downloaded filenames
SCHOOL_YEAR = "23-24"

# ==========================================

def run_save_and_export(page):
    print("Resuming script... Processing CSV file.")

    csv_file_path = 'section_export.csv'
    try:
        # Use utf-8-sig to handle potential BOM from Excel exports
        with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Check for 'Section NID' in fieldnames (stripping potential whitespace)
            fieldnames = [name.strip() for name in reader.fieldnames] if reader.fieldnames else []
            
            if 'Section NID' not in fieldnames:
                print(f"Error: 'Section NID' column not found in {csv_file_path}.")
                print(f"Available columns: {fieldnames}")
                return
            
            # Load all rows into memory
            csv_rows = list(reader)
            
        # Phase 1: Save ALL courses to Resources
        print("\n" + "="*50)
        print(f"PHASE 1: Saving {len(csv_rows)} courses to Resources...")
        print("="*50 + "\n")
        
        successful_saves = 0
        
        for index, row in enumerate(csv_rows):
            # Robustly get the value, handling potential key whitespace issues
            section_nid = row.get('Section NID')
            if not section_nid:
                    # Fallback if key has whitespace
                    for key in row.keys():
                        if key and key.strip() == 'Section NID':
                            section_nid = row[key]
                            break
            course_name = row.get('Course Name', 'Unknown Course')
            
            if not section_nid:
                print(f"Skipping row with missing Section NID: {row}")
                continue
            
            # Construct URL
            course_url = f"https://YOURSCHOOLOGYDOMAIN/course/{section_nid}/materials"
            print(f"Processing [{index+1}/{len(csv_rows)}] {course_name} (NID: {section_nid})...")
            
            try:
                # Go to course materials page
                page.goto(course_url)
                
                # Wait for page to load sufficiently
                page.wait_for_load_state('domcontentloaded')
                time.sleep(1)

                # 1. Click "Options" dropdown
                try:
                    page.wait_for_selector('#toolbar-options-wrapper', state='visible', timeout=10000)
                    page.click('#toolbar-options-wrapper')
                    time.sleep(1)
                except Exception as e:
                    print(f"  - Error finding 'Options' menu: {e}. Skipping...")
                    continue

                # 2. Click "Save Course to Resources"
                try:
                    page.wait_for_selector('#save-folders-to-resources a', state='visible', timeout=5000)
                    page.click('#save-folders-to-resources a')
                    time.sleep(1)
                except Exception as e:
                    print(f"  - Error finding 'Save Course to Resources' option: {e}. Skipping...")
                    continue

                # 3. Click "Submit" on the confirmation/settings page
                try:
                    page.wait_for_selector('input#edit-submit', state='visible', timeout=10000)
                    page.click('input#edit-submit')
                    page.wait_for_load_state('networkidle')
                    time.sleep(1)
                    print(f"  - Saved to Resources successfully.")
                    successful_saves += 1
                    
                except Exception as e:
                    print(f"  - Error clicking 'Submit' (Save to Resources): {e}. Skipping...")
                    continue
                    
            except Exception as e:
                print(f"  - Unexpected error processing course {section_nid}: {e}")
                
            # Small delay
            time.sleep(1)

        # Phase 2: Export ALL courses
        print("\n" + "="*50)
        print(f"PHASE 2: Exporting {successful_saves} courses (Common Cartridge)...")
        print("="*50 + "\n")
        
        if successful_saves == 0:
            print("No courses were saved successfully. Skipping export.")
            return

        current_export_index = 0
        
        # We loop as many times as we have successful saves, assuming each save added one valid entry.
        for i in range(successful_saves):
            try:
                print(f"Starting Export for item index {current_export_index}...")
                
                # A. Go to Resources
                page.goto("https://YOURSCHOOLOGYDOMAIN/resources")
                page.wait_for_load_state('networkidle')
                time.sleep(1)

                # B. Click "Collection Options" dropdown (Next to My Resources)
                try:
                    # Find the export link (hidden) to locate the correct wrapper
                    # We use a robust wait here because navigation just happened
                    page.wait_for_selector('a[href*="/resources/my/collection/export"]', state='attached', timeout=10000)
                    
                    wrapper = page.locator('.action-links-wrapper:has(a[href*="/resources/my/collection/export"])')
                    dropdown_trigger = wrapper.locator('.action-links-unfold')
                    
                    if dropdown_trigger.count() > 0:
                        dropdown_trigger.click()
                        time.sleep(1)
                    else:
                        # Fallback
                        page.locator('.action-links-unfold').first.click()
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"    - Error finding Collection Options dropdown: {e}. Trying fallback...")
                    try:
                        page.locator('.action-links-unfold').first.click()
                        time.sleep(1)
                    except:
                        pass

                # C. Click "Export" link
                page.wait_for_selector('a[href*="/resources/my/collection/export"]', state='visible', timeout=5000)
                page.locator('a[href*="/resources/my/collection/export"]').click()
                time.sleep(1)

                # D. Handle Folder Selection (The Core Requirement)
                # Wait for the dropdown
                page.wait_for_selector('#edit-folder-select', state='visible', timeout=10000)
                
                # Get all option elements
                options_data = page.evaluate("""() => {
                    const select = document.querySelector('#edit-folder-select');
                    return Array.from(select.options).map(o => ({
                        value: o.value,
                        text: o.text,
                        trimmed_text: o.text.trim()
                    }));
                }""",)
                
                # Filter options:
                # 1. Ignore value "0" ((No Folder))
                # 2. Ignore text starting with "--"
                valid_options = []
                for opt in options_data:
                    if opt['value'] == '0':
                        continue
                    if opt['trimmed_text'].startswith('--'):
                        continue
                    valid_options.append(opt)
                
                # Check if current_export_index is valid
                if current_export_index < len(valid_options):
                    target_option = valid_options[current_export_index]
                    print(f"    - Selecting option [{current_export_index}]: {target_option['trimmed_text']} (Value: {target_option['value']})")
                    
                    # Select the option
                    page.select_option('#edit-folder-select', target_option['value'])
                    time.sleep(1)
                    
                    # E. Click "Export" (Submit)
                    page.wait_for_selector('input#edit-submit[value="Export"]', state='visible', timeout=5000)
                    page.click('input#edit-submit[value="Export"]')
                    time.sleep(1)
                    
                    # F. Wait for reload/completion
                    page.wait_for_load_state('networkidle')
                    print(f"    - Export initiated successfully.")
                    
                    # Increment counter ONLY on success
                    current_export_index += 1

                    # G. Delay to avoid rate limiting
                    print("    - Waiting 10 seconds before next export to avoid Schoology request blocks...")
                    time.sleep(10)
                    
                else:
                    print(f"    - Error: current_export_index ({current_export_index}) is out of bounds for valid options list (size: {len(valid_options)}).")
                    pass
                    
            except Exception as e:
                print(f"  - Error during Export flow for index {current_export_index}: {e}")
                pass

    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred in Mode 1: {e}")

def run_download_transfers(page):
    print("\n" + "="*50)
    print("MODE 2: Downloading Transfers")
    print("="*50 + "\n")
    
    transfers_url = "https://YOURSCHOOLOGYDOMAIN/settings/transfers"
    print(f"Navigating to {transfers_url}...")
    page.goto(transfers_url)
    page.wait_for_load_state('networkidle')
    
    # Locate the list of items
    # Requirement mentions <div class="item-list">.
    # We will look for rows. In Schoology transfers, it's often a table.
    
    # NEW: Click "View More" until all items are loaded
    print("Checking for 'More' button to load all items...")
    while True:
        try:
            more_button = page.locator('.more-btn')
            if more_button.is_visible(timeout=5000):
                print("  - Clicking 'More' button...")
                more_button.click()
                # Wait for the new items to load (ajax)
                page.wait_for_load_state('networkidle')
                # Brief pause to let DOM settle
                time.sleep(2)
            else:
                print("  - 'More' button no longer visible. All items loaded.")
                break
        except Exception as e:
            print(f"  - Finished loading items or encountered error: {e}")
            break

    # Find all list items (rows)
    # Based on HTML provided: <li class="s-base-list_list-item ...">
    items = page.locator('li.s-base-list_list-item').all()
    
    print(f"Found {len(items)} transfer items.")
    
    if len(items) == 0:
        print("No transfer items found.")
        return

    # Ensure download directory exists
    download_path = Path(DOWNLOAD_DIR)
    download_path.mkdir(parents=True, exist_ok=True)
    print(f"Saving downloads to: {download_path.absolute()}")

    download_counter = 0

    # Iterate through each row item
    for i in range(len(items)):
        try:
            print(f"\nChecking item {i+1}/{len(items)}...")
            
            # Re-locate the specific row item to be safe
            current_item = page.locator('li.s-base-list_list-item').nth(i)
            
            # Find the gear icon within this item
            trigger = current_item.locator('.action-links-unfold')
            
            if not trigger.is_visible():
                print("  - No settings gear found for this item.")
                continue

            # Scroll row into view
            current_item.scroll_into_view_if_needed()
            
            # Click to open dropdown
            trigger.click()
            
            # Look for 'Download' link specifically WITHIN this item's dropdown
            # The dropdown is inside the row structure per the HTML provided:
            # <div class="action-links-wrapper ...">
            #   <ul class="action-links ..."> ... <a ...>Download</a> ... </ul>
            # </div>
            download_link = current_item.locator('ul.action-links a:has-text("Download")')
            
            try:
                # Wait for it to become visible
                download_link.wait_for(state='visible', timeout=3000)
                
                print("  - Download option found. Initiating download...")
                
                with page.expect_download() as download_info:
                    download_link.click()
                
                download = download_info.value
                # Suggested filename
                suggested_filename = download.suggested_filename
                
                # Increment counter for unique identifier
                download_counter += 1
                
                # Extract base name and extension
                base_name, ext = os.path.splitext(suggested_filename)
                
                # New filename including School Year and a unique counter
                new_filename = f"{base_name}_{SCHOOL_YEAR}_{download_counter}{ext}"
                destination = download_path / new_filename
                
                print(f"  - Downloading to {destination}...")
                download.save_as(destination)
                
                print("  - Download complete.")
                
                # Requirement: Wait 10 seconds
                print("  - Waiting 10 seconds as requested...")
                time.sleep(10)

            except Exception as e:
                # Timeout or other error -> Download link not found or not clickable
                print(f"  - No 'Download' option found or accessible for this item: {e}")
                
            # Close dropdown to reset state for next item
            # Clicking the body (0,0) usually closes open dropdowns
            page.mouse.click(0, 0)
            # Brief pause to allow UI to settle
            time.sleep(1)
            
        except Exception as e:
            print(f"  - Error processing item {i}: {e}")
            # Ensure we close dropdown even on error if possible
            try:
                page.mouse.click(0, 0)
            except:
                pass
            continue

def run():
    print("Starting Schoology Automation...")
    print(f"Current MODE: {MODE}")
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode so user can see and log in
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Login step
        print("Navigating to login page...")
        try:
            page.goto("https://YOURSCHOOLOGYDOMAIN/login")
        except Exception as e:
            print(f"Error navigating to login: {e}")
            return

        print("\n" + "="*50)
        print("ACTION REQUIRED: Please log in to Schoology in the opened browser window.")
        print("Once logged in and ready, click the 'Resume' button in the Playwright Inspector")
        print("or close the inspector window to continue (if using python input to resume).")
        print("Script is paused...")
        print("="*50 + "\n")
        
        # Pause script execution to allow manual login
        page.pause()
        
        if MODE == 1:
            run_save_and_export(page)
        elif MODE == 2:
            run_download_transfers(page)
        else:
            print(f"Invalid MODE selected: {MODE}")

        print("Closing browser...")
        browser.close()
        print("Done.")

if __name__ == "__main__":
    run()