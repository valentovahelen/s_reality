from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import pandas as pd
import datetime
import tempfile

# variables
price_max = 5_500_000
sqm_min = 40
floor_min = 2
dispozice_list = ["2+kk", "2+1", "3+kk", "3+1"]
today = datetime.date.today()

# Stealth Settings -----------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    profile_path = r"C:\Users\H32250\AppData\Roaming\\MEdge\\Profiles"

    temp_profile_dir = tempfile.mkdtemp()

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)

    # Website ----------------------------------------------------------------------------------------------------------------------------
    # Define Target URL
    base_url = "https://www.sreality.cz/hledani/filtr/byty"
    driver.get(base_url)
    time.sleep(random.uniform(1, 4))  

    # Check if we are being blocked
    print(f"Page title: {driver.title}")
    if "Access" in driver.title or " blocked" in driver.page_source.lower():
        print("WARNING: Sreality.cz has blocked the request!")
        driver.quit()
        exit()

    # Add
    try:
        add = driver.find_element(By.CSS_SELECTOR, ".szn-cmp-dialog-container").click()
        actions  = ActionChains(driver)
        actions.send_keys(Keys.TAB).perform()
        actions.key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT).perform() # shift 2x protože spustí a pak pustí
        actions.key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT).perform()
        actions.send_keys(Keys.ENTER).perform()
        print("Prošlo personalizací")
    except:
        print("Failed due to add.")

    # Filtering information -----------------------------------------------------------------------------------------------------------------
    
    try:
        # typ nabídky
        element = WebDriverWait(driver, timeout=10).until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Prodej']")))
        typ_nabidky = driver.find_element(By.XPATH, "//span[normalize-space()='Prodej']")
        typ_nabidky.click()
        print("Typ nabídky:", typ_nabidky.get_attribute("innerHTML"))
        # kontrola print("Zobrazen:", checkbox.is_displayed()); print("Aktivní:", checkbox.is_enabled())
        
        # dispozice
        time.sleep(1)
        for disp in dispozice_list:
            dispozice = driver.find_element(By.XPATH, f"//span[normalize-space()='{disp}']")
            dispozice.click()
            print("Dispozice:", dispozice.get_attribute("innerHTML"))

        # lokalita
        lokalita = driver.find_element(By.XPATH, "//*[name()='path' and contains(@d,'M546.667 3')]")
        lokalita.click()
        """lokalita.send_keys("Brno")
        lokalita.send_keys(Keys.ARROW_DOWN)
        lokalita.send_keys(Keys.ENTER)"""
        mesto = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//span[contains(text(),'Brno-město')]")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", mesto) # bez scroll nebylo ve viewportu
        mesto.click()
        mesto_value = mesto.get_attribute("value")
        print("Lokalita:", mesto_value)

        # podlaží
        podlazi = driver.find_element(By.ID, "«r0»")
        podlazi.send_keys(floor_min)
        podlazi_value = podlazi.get_attribute("value")
        print("Podlaží od:", podlazi_value)
        
        # užitná plocha
        plocha = driver.find_element(By.ID, "«r2»")
        plocha.send_keys(sqm_min)
        plocha_value = plocha.get_attribute("value")
        print("Užitná plocha od:", plocha_value)

        # cena
        cena = driver.find_element(By.ID, "«r5»")
        cena.send_keys(price_max)
        cena_value = cena.get_attribute("value")
        print("Cena do:", cena_value)

        # nabídky - enter
        nabidky = driver.find_element(By.ID, "«Ralal6lff6»")
        nabidky.click()
        time.sleep(5)

    except:
        print("Failed due to filtering infromation")

    # Scraping RealEstate information ---------------------------------------------------------------------------------------------------

    # Extract Property Listings
    scraped_data = []
    page_number = 1
    price_number = 0
    listings_number = driver.find_element(By.XPATH, '//*[contains(text(), "výsledků")]').text.strip() # //* — najdi jakýkoliv element
    listings_number = int(listings_number.split(" ")[0])

    while True:
        print(f"Scraping page {page_number}...")

        # Locate the main listings container
        try:
            container = driver.find_element(By.CSS_SELECTOR, '[data-e2e="estates-list"]')
            listings = container.find_elements(By.CSS_SELECTOR, ":scope > li") # jak získat jen přímé <li> potomky
        except:
            print("Failed to locate the property list container. Exiting...")
            break

        print(f"Found {len(listings)} listings on page {page_number}")

        for listing in listings:

            # Extract price     
            try:
                price = listing.find_element(By.XPATH, './/a/div[2]/div/div/p[3]').text.strip() # nebyl žadný identifikátor muselo se podle html struktury
                # indexování v XPATH od 1
                # šlo by něco i ve stylu (By.XPATH, './/a//p[contains(text(), "Kč")]')
                # // — značí hledání v celém podstromu
                # //p znamená „najdi všechny <p> kdekoli v dokumentu (nebo relativně k aktuálnímu uzlu)
                # / — značí přesnou další úroveň (přímý potomek)
                # . — aktuální uzel
                # .//p znamená „najdi všechny <p> v podstromu aktuálního elementu
                price_number += 1
            except:
                price = "N/A"

            # Extract address     
            try:
                address = listing.find_element(By.XPATH, './/a/div[2]/div/div/p[2]').text.strip()
            except:
                address = "N/A"

            # Extract disposition and sqm  
            try:
                disposition_sqm = listing.find_element(By.XPATH, './/a/div[2]/div/div/p[1]').text.strip()
                disposition_sqm = disposition_sqm.split(" m²")[0].split("Prodej bytu ")[1]
                disposition = disposition_sqm.split(" ")[0]
                sqm = int(disposition_sqm.split(" ")[1])
            except:
                disposition_sqm = "N/A"
                disposition = "N/A"
                sqm = "N/A"

            # Extract listing link
            try:
                link = listing.find_element(By.TAG_NAME, "a")
                link = link.get_attribute('href')
                link = f"https://www.sreality.cz{link}" if link.startswith("/") else link
            except:
                print("Skipping a listing due to missing link data")
                continue  # Skip listings with missing elements

            # Extract image URL
            try:
                image_element = listing.find_element(By.TAG_NAME, "img")
                image_url = image_element.get_attribute("src")
            except:
                image_url = "N/A"

            # Store the data
            scraped_data.append({
                "Price": price,
                "Address": address,
                "Disposition": disposition,
                "m2": sqm,
                "Link": link,
                "Image URL": image_url, 
            })

        # Pagination: Check if a "Next Page" button exists
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, '[data-e2e="show-more-btn"]')
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
            next_button.click()
            page_number += 1
            time.sleep(random.uniform(1, 3))
            # na stránce se furt měnilo - bylo potřeba jít přes data-e2e (end to end) je vlastní HTML atribut, který vývojáři přidávají do komponent 
            # hlavně pro automatizované testy nebo scrapping - v html
            # 1 data-e2e
            # 2 aria-label - Accessible Rich Internet Applications - označení účelu nebo popisu prvku pro čtečky obrazovky - (By.XPATH, "//button[@aria-label='Další stránka']")
            # 3 viditelný text - (By.XPATH, "//button[text()='Další stránka']")
        except:
            print("No more pages. Scraping complete.")
            break

    # comparation - number of listings
    if listings_number == price_number:
        print(f"Good, all {price_number} listings match.")
    else:
        print(f"Opps there is a mistake.\nNumber of listings from the website: {listings_number}\nNumber of listing from the code: {price_number} ")

    time.sleep(10)

    # Saving Data -------------------------------------------------------------------------------------------------------
    df = pd.DataFrame(scraped_data)
    df = df[df["Price"] != "N/A"] # nebo df = df.drop(df[df["Price"] == "N/A"].index)
    df.to_csv("s_reality.csv", index=False)
    print(f"{len(df)} listings saved!")

    driver.quit()
     

    # Notes - other ------------------------------------------------------------------------------------------------------
    # rozdíl mez css class (besic) a css selector (možno kombinovat s jinými elementy)
    # <button class="btn primary" id="submit-btn">OK</button>
    #   -> class: "btn primary"
    #   -> selector:    .btn (vybere všechny s třídou btn)
    #                   button.primary (vybere všechny <button>, co mají třídu primary)
    #                   #submit-btn (vybere element s id submit-btn)
