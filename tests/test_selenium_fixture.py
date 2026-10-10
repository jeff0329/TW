"""使用本地動態 HTML 驗證 Selenium，不依賴第三方旅遊網站。"""

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


FIXTURE = Path(__file__).with_name("selenium_fixture.html")


def main() -> None:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(FIXTURE.as_uri())
        cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-card"))
        )
        assert len(cards) == 3, f"expected 3 cards, got {len(cards)}"
        assert cards[2].find_element(By.CSS_SELECTOR, ".product-title").text == "故宮博物院導覽"
        assert cards[0].find_element(By.CSS_SELECTOR, ".price").text == "NT$1,200"
        assert cards[1].find_element(By.CSS_SELECTOR, ".location").text == "新北市"
        print("local Selenium fixture passed: 3 dynamic cards")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
