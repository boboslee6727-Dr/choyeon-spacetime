from playwright.sync_api import sync_playwright

URL = "https://choyeon-spacetime.streamlit.app/?mode=order"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(URL, timeout=90000)
    pg.wait_for_timeout(8000)
    btn = pg.get_by_role("button", name="Yes, get this app back up!")
    if btn.count() > 0:
        print("앱이 잠들어 있어서 깨웠습니다")
        btn.first.click()
        pg.wait_for_timeout(60000)
    else:
        print("앱이 이미 깨어 있습니다")
        pg.wait_for_timeout(20000)
    b.close()
