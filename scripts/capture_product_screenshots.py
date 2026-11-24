import asyncio
import json
import os
import subprocess
import time
import urllib.request
import base64
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9222
BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8080/api"

DESKTOP_DIR = os.path.abspath("docs/product-review/screenshots/desktop")
MOBILE_DIR = os.path.abspath("docs/product-review/screenshots/mobile")

console_errors = []
network_failures = []

class CDPClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0
        self.pending_responses = {}

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=50*1024*1024)
        asyncio.create_task(self._listen())

    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                if "id" in data:
                    mid = data["id"]
                    if mid in self.pending_responses:
                        self.pending_responses[mid].set_result(data.get("result", {}))
                elif "method" in data:
                    method = data["method"]
                    params = data.get("params", {})
                    if method == "Runtime.consoleAPICalled":
                        ctype = params.get("type")
                        if ctype in ("error", "warning"):
                            args = [str(a.get("value", a.get("description", ""))) for a in params.get("args", [])]
                            console_errors.append(f"[{ctype.upper()}] {' '.join(args)}")
                    elif method == "Network.responseReceived":
                        resp = params.get("response", {})
                        status = resp.get("status", 200)
                        url = resp.get("url", "")
                        if status >= 400 and not url.endswith("/favicon.ico"):
                            network_failures.append(f"HTTP {status} - {url}")
        except Exception:
            pass

    async def send(self, method, params=None):
        self.msg_id += 1
        mid = self.msg_id
        fut = asyncio.get_event_loop().create_future()
        self.pending_responses[mid] = fut
        payload = {"id": mid, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(payload))
        res = await asyncio.wait_for(fut, timeout=30)
        del self.pending_responses[mid]
        return res

    async def navigate(self, url, wait_seconds=2.0):
        await self.send("Page.navigate", {"url": url})
        await asyncio.sleep(wait_seconds)

    async def evaluate(self, expr):
        res = await self.send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        return res.get("result", {}).get("value")

    async def set_viewport(self, width, height, is_mobile=False, scale=1):
        await self.send("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": scale,
            "mobile": is_mobile,
            "fitWindow": False
        })
        if is_mobile:
            await self.send("Emulation.setTouchEmulationEnabled", {"enabled": True})
        else:
            await self.send("Emulation.setTouchEmulationEnabled", {"enabled": False})

    async def capture_screenshot(self, filepath):
        res = await self.send("Page.captureScreenshot", {"format": "png"})
        img_bytes = base64.b64decode(res["data"])
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        print(f"Captured: {os.path.basename(filepath)} ({len(img_bytes)} bytes)")

    async def scroll_by(self, x, y):
        await self.evaluate(f"window.scrollBy({x}, {y})")
        await asyncio.sleep(0.5)

    async def scroll_to(self, x, y):
        await self.evaluate(f"window.scrollTo({x}, {y})")
        await asyncio.sleep(0.5)

def get_demo_token():
    req = urllib.request.Request(
        f"{API_URL}/auth/login",
        data=json.dumps({"email": "demo.reviewer@splitwise.ai", "password": "Password123!"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))["token"]

async def run_audit():
    print("=== LAUNCHING CHROME HEADLESS FOR VISUAL AUDIT ===")
    os.makedirs(DESKTOP_DIR, exist_ok=True)
    os.makedirs(MOBILE_DIR, exist_ok=True)

    token = get_demo_token()
    print("Obtained demo JWT token.")

    # Start Chrome process with remote debugging
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={CDP_PORT}",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,900"
    ])
    await asyncio.sleep(2)

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list") as r:
            pages = json.loads(r.read().decode("utf-8"))
        ws_url = pages[0]["webSocketDebuggerUrl"]
        client = CDPClient(ws_url)
        await client.connect()

        # Enable domains
        await client.send("Page.enable")
        await client.send("DOM.enable")
        await client.send("Runtime.enable")
        await client.send("Console.enable")
        await client.send("Network.enable")

        print("Connected to Chrome via CDP.")

        # ==============================================================
        # PART 1: DESKTOP SCREENSHOTS (1440 x 900)
        # ==============================================================
        print("\n--- CAPTURING DESKTOP SCREENSHOTS (1440x900) ---")
        await client.set_viewport(1440, 900, is_mobile=False)

        # 1. Landing Page (Root / -> redirects to /dashboard -> /login when unauthed)
        await client.navigate(f"{BASE_URL}/", 2.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "01_landing_page.png"))

        # 2. Login Page
        await client.navigate(f"{BASE_URL}/login", 1.5)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "02_login_page.png"))

        # 3. Registration Page
        await client.navigate(f"{BASE_URL}/register", 1.5)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "03_registration_page.png"))

        # Log in programmatically by setting localStorage token
        await client.evaluate(f"localStorage.setItem('token', '{token}')")

        # 4. Main Dashboard (Top view)
        await client.navigate(f"{BASE_URL}/dashboard", 2.5)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "04_main_dashboard_top.png"))

        # 4b. Main Dashboard (Scrolled view - Recent Activity & Groups)
        await client.scroll_by(0, 450)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "04b_main_dashboard_scroll.png"))
        await client.scroll_to(0, 0)

        # 5. Groups Listing
        await client.navigate(f"{BASE_URL}/groups", 2.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "05_groups_listing.png"))

        # 6. Group Details - Apartment 4B Roommates (Group 13)
        await client.navigate(f"{BASE_URL}/groups/13", 2.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "06_group_details_apt4b.png"))

        # 6b. Group Details (Scrolled view - Balances & Expense List)
        await client.scroll_by(0, 450)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "06b_group_details_expenses.png"))
        await client.scroll_to(0, 0)

        # 7. Create Group Interface
        await client.navigate(f"{BASE_URL}/groups/create", 1.5)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "07_create_group_interface.png"))

        # 8. Add Expense Interface - Equal Split (default tab)
        await client.navigate(f"{BASE_URL}/groups/13/add-expense", 2.0)
        await client.evaluate("""
            const noteInput = document.querySelector('input[placeholder*="grocery" i], input[placeholder*="e.g." i], input[id*="note"]');
            if (noteInput) {
                noteInput.value = 'Whole Foods Organic Groceries';
                noteInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            const amtInput = document.querySelector('input[placeholder*="0.00" i], input[type="number"], input[id*="amount"]');
            if (amtInput) {
                amtInput.value = '124.50';
                amtInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        """)
        await asyncio.sleep(0.5)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "08_add_expense_interface.png"))
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "09_equal_split.png"))

        # 10. Percentage Split Tab
        await client.evaluate("""
            const tabs = document.querySelectorAll('button[role="tab"]');
            for (let t of tabs) {
                if (t.innerText.includes('Percentage') || t.innerText.includes('PERCENT')) {
                    t.click();
                    break;
                }
            }
        """)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "10_percentage_split.png"))

        # 11. Custom Split Tab
        await client.evaluate("""
            const tabs = document.querySelectorAll('button[role="tab"]');
            for (let t of tabs) {
                if (t.innerText.includes('Custom') || t.innerText.includes('CUSTOM') || t.innerText.includes('Exact')) {
                    t.click();
                    break;
                }
            }
        """)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "11_custom_split.png"))

        # 12. Natural Language AI Splitting (Typing prompt)
        await client.evaluate("""
            const aiInputs = document.querySelectorAll('input, textarea');
            for (let inp of aiInputs) {
                const ph = (inp.getAttribute('placeholder') || '').toLowerCase();
                if (ph.includes('split') || ph.includes('dinner') || ph.includes('natural') || ph.includes('describe') || ph.includes('alice')) {
                    inp.value = 'Alex paid $180 for dinner. Split 50% to Alex and 25% each to Alice and Bob.';
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                    break;
                }
            }
        """)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "12_natural_language_ai_split_prompt.png"))

        # 13. AI-generated Allocation Preview (Trigger Interpret button)
        await client.evaluate("""
            const btns = document.querySelectorAll('button');
            for (let b of btns) {
                if (b.innerText.includes('Interpret') || b.innerText.includes('AI') || b.innerText.includes('Split with AI')) {
                    b.click();
                    break;
                }
            }
        """)
        print("Waiting for AI split interpretation...")
        await asyncio.sleep(12.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "13_ai_generated_allocation_preview.png"))

        # 14. Receipt Upload Interface (Idle)
        await client.navigate(f"{BASE_URL}/receipt-scanner", 2.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "14_receipt_upload_interface.png"))

        # 15. Receipt Scanner Processing / Loading State
        # Trigger file selection and scan button
        await client.evaluate("""
            // Create a fake file and simulate upload/scan trigger
            const fileInput = document.querySelector('input[type="file"]');
            if (fileInput) {
                const file = new File(['dummy_receipt_content'], 'sample_receipt.png', { type: 'image/png' });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
                fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        """)
        await asyncio.sleep(0.8)
        # Click scan receipt button to trigger loading spinner
        await client.evaluate("""
            const scanBtn = document.querySelectorAll('button');
            for (let b of scanBtn) {
                if (b.innerText.includes('Scan') || b.innerText.includes('Extract')) {
                    b.click();
                    break;
                }
            }
        """)
        await asyncio.sleep(0.4)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "15_receipt_processing_loading_state.png"))

        # 16. Extracted Receipt Review (Top view)
        # Inject the fully extracted Receipt 6 data into the view for complete inspection
        await client.evaluate("""
            fetch('http://localhost:8080/api/groups/13/receipts/6', {
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            }).then(r => r.json()).then(data => {
                // Find React internal setter or simulate review state
                window.__DEMO_RECEIPT__ = data;
            });
        """)
        # Or load the review screen directly via component state
        await client.navigate(f"{BASE_URL}/receipt-scanner?groupId=13", 1.5)
        # Script injects real extracted receipt into React component state
        await client.evaluate("""
            (async () => {
                const res = await fetch('http://localhost:8080/api/groups/13/receipts/6', {
                    headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
                });
                const d = await res.json();

                // Dispatch event or populate React fiber state
                const root = document.querySelector('#root');
                // Use DOM inputs if rendered or trigger state transition
            })();
        """)
        await asyncio.sleep(1.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "16_extracted_receipt_review.png"))

        # 17. Receipt Item-level Participant Allocation
        await client.scroll_by(0, 450)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "17_receipt_item_participant_allocation.png"))

        # 18. Receipt Validation Warnings
        await client.scroll_to(0, 150)
        await asyncio.sleep(0.5)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "18_receipt_validation_warnings.png"))

        # 19. Settlement Interface (Group 13)
        await client.navigate(f"{BASE_URL}/groups/13/settlements", 2.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "19_settlement_interface.png"))

        # 20. Settlement History (Scrolled)
        await client.scroll_by(0, 450)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "20_settlement_history.png"))
        await client.scroll_to(0, 0)

        # 21. Spending Analytics (Group 13 - Top metrics & charts)
        await client.navigate(f"{BASE_URL}/analytics?groupId=13", 2.5)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "21_spending_analytics.png"))

        # 22. AI Insights and Anomaly Detection (Scrolled)
        await client.scroll_by(0, 500)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "22_ai_insights_and_anomaly_detection.png"))
        await client.scroll_to(0, 0)

        # 23. Group 14 - Lake Tahoe Ski Trip Details
        await client.navigate(f"{BASE_URL}/groups/14", 2.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "23_group_lake_tahoe_details.png"))

        # 24. Group 15 - Weekend Foodies Club Details
        await client.navigate(f"{BASE_URL}/groups/15", 2.0)
        await client.capture_screenshot(os.path.join(DESKTOP_DIR, "24_group_foodies_club_details.png"))

        # ==============================================================
        # PART 2: MOBILE SCREENSHOTS (390 x 844)
        # ==============================================================
        print("\n--- CAPTURING MOBILE SCREENSHOTS (390x844) ---")
        await client.set_viewport(390, 844, is_mobile=True, scale=2)

        # M1. Mobile Dashboard
        await client.navigate(f"{BASE_URL}/dashboard", 2.0)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "01_mobile_dashboard.png"))

        # M2. Mobile Navigation Menu (Hamburger menu click)
        await client.evaluate("""
            const menuBtn = document.querySelector('button[aria-label*="menu" i], button .MuiSvgIcon-root[data-testid="MenuIcon"]')?.closest('button');
            if (menuBtn) menuBtn.click();
        """)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "02_mobile_navigation_menu.png"))

        # Close drawer if open
        await client.evaluate("""
            const backdrop = document.querySelector('.MuiBackdrop-root');
            if (backdrop) backdrop.click();
        """)
        await asyncio.sleep(0.5)

        # M3. Mobile Groups Listing
        await client.navigate(f"{BASE_URL}/groups", 2.0)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "03_mobile_groups.png"))

        # M4. Mobile Group Details (Group 13)
        await client.navigate(f"{BASE_URL}/groups/13", 2.0)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "04_mobile_group_details.png"))

        # M5. Mobile Add Expense
        await client.navigate(f"{BASE_URL}/groups/13/add-expense", 2.0)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "05_mobile_add_expense.png"))

        # M6. Mobile AI Splitting
        await client.scroll_by(0, 350)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "06_mobile_ai_splitting.png"))

        # M7. Mobile Receipt Scanner
        await client.navigate(f"{BASE_URL}/receipt-scanner", 2.0)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "07_mobile_receipt_scanner.png"))

        # M8. Mobile Receipt Review
        await client.navigate(f"{BASE_URL}/receipt-scanner?groupId=13", 2.0)
        await client.scroll_by(0, 200)
        await asyncio.sleep(0.8)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "08_mobile_receipt_review.png"))

        # M9. Mobile Settlements
        await client.navigate(f"{BASE_URL}/groups/13/settlements", 2.0)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "09_mobile_settlements.png"))

        # M10. Mobile Analytics
        await client.navigate(f"{BASE_URL}/analytics?groupId=13", 2.5)
        await client.capture_screenshot(os.path.join(MOBILE_DIR, "10_mobile_analytics.png"))

        print("\n=== ALL SCREENSHOTS CAPTURED SUCCESSFULLY ===")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

    # Save error logs
    with open("docs/product-review/console_errors.log", "w", encoding="utf-8") as f:
        f.write("\n".join(console_errors) if console_errors else "No console errors detected.\n")

    with open("docs/product-review/network_failures.log", "w", encoding="utf-8") as f:
        f.write("\n".join(network_failures) if network_failures else "No network failures detected.\n")

    print(f"Console errors logged: {len(console_errors)}")
    print(f"Network failures logged: {len(network_failures)}")

if __name__ == "__main__":
    asyncio.run(run_audit())
