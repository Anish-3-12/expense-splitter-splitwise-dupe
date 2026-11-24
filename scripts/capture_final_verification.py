import asyncio
import json
import os
import subprocess
import time
import urllib.request
import base64
import websockets
import tempfile

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9225
BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8080/api"
OUT_DIR = os.path.abspath("docs/product-review/final-verification")

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
        except Exception:
            pass

    async def send(self, method, params=None):
        self.msg_id += 1
        mid = self.msg_id
        fut = asyncio.get_event_loop().create_future()
        self.pending_responses[mid] = fut
        payload = {"id": mid, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(payload))
        res = await asyncio.wait_for(fut, timeout=60)
        del self.pending_responses[mid]
        return res

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
        await self.send("Emulation.setTouchEmulationEnabled", {"enabled": is_mobile})

    async def wait_for_ready(self, max_wait=10.0):
        expr = """
            new Promise((resolve) => {
                const start = Date.now();
                const check = () => {
                    const spinner = document.querySelector('.MuiCircularProgress-root');
                    const hasContent = document.querySelector('form, main, h1, h2, h3, h4, h5, h6, table, .MuiCard-root, button');
                    if (!spinner && hasContent) {
                        resolve(true);
                    } else if (Date.now() - start > 10000) {
                        resolve(false);
                    } else {
                        setTimeout(check, 100);
                    }
                };
                check();
            });
        """
        await self.evaluate(expr)
        await asyncio.sleep(1.0)

    async def navigate_and_wait(self, url):
        await self.send("Page.navigate", {"url": url})
        await self.wait_for_ready()

    async def capture(self, filename):
        filepath = os.path.join(OUT_DIR, filename)
        res = await self.send("Page.captureScreenshot", {"format": "png"})
        img_bytes = base64.b64decode(res["data"])
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        print(f"Captured: {filename} ({len(img_bytes)} bytes)")

def get_demo_token():
    req = urllib.request.Request(
        f"{API_URL}/auth/login",
        data=json.dumps({"email": "demo.reviewer@splitwise.ai", "password": "Password123!"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))["token"]

async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    token = get_demo_token()
    user_data_dir = tempfile.mkdtemp(prefix="chrome_final_verify_")

    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,800"
    ])
    await asyncio.sleep(2)

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list") as r:
            ws_url = json.loads(r.read().decode("utf-8"))[0]["webSocketDebuggerUrl"]
        client = CDPClient(ws_url)
        await client.connect()
        await client.send("Page.enable")
        await client.send("Runtime.enable")
        await client.send("DOM.enable")

        # Set auth token in localStorage
        await client.send("Page.navigate", {"url": f"{BASE_URL}/login"})
        await asyncio.sleep(1)
        await client.evaluate(f"localStorage.setItem('token', '{token}')")

        # -------------------------------------------------------------
        # 1. Desktop Dashboard (1280x800)
        # -------------------------------------------------------------
        print("\n--- 1. Desktop Dashboard ---")
        await client.set_viewport(1280, 800, is_mobile=False)
        await client.navigate_and_wait(f"{BASE_URL}/dashboard")
        await client.capture("01_desktop_dashboard.png")

        # -------------------------------------------------------------
        # 2. Mobile Dashboard (375x812)
        # -------------------------------------------------------------
        print("\n--- 2. Mobile Dashboard ---")
        await client.set_viewport(375, 812, is_mobile=True)
        await client.navigate_and_wait(f"{BASE_URL}/dashboard")
        await client.capture("02_mobile_dashboard.png")

        # -------------------------------------------------------------
        # 3 & 4. Desktop Settlements Layout & History (1280x800)
        # -------------------------------------------------------------
        print("\n--- 3 & 4. Desktop Settlements ---")
        await client.set_viewport(1280, 800, is_mobile=False)
        await client.navigate_and_wait(f"{BASE_URL}/groups/13/settlements")
        await client.capture("03_desktop_settlements_layout.png")
        await client.evaluate("window.scrollTo(0, 200)")
        await asyncio.sleep(0.5)
        await client.capture("04_desktop_settlements_history.png")

        # -------------------------------------------------------------
        # 5. Lake Tahoe Details - Expense 21 categorized as Travel
        # -------------------------------------------------------------
        print("\n--- 5. Lake Tahoe Expense 21 ---")
        await client.set_viewport(1280, 800, is_mobile=False)
        await client.navigate_and_wait(f"{BASE_URL}/groups/14")
        await client.capture("05_lake_tahoe_expense_21_travel.png")

        # -------------------------------------------------------------
        # 6, 7 & 8. Add Expense Natural Language Interpretation
        # -------------------------------------------------------------
        print("\n--- 6. Add Expense AI Prompt Entered ---")
        await client.set_viewport(1280, 800, is_mobile=False)
        await client.navigate_and_wait(f"{BASE_URL}/groups/13/add-expense")

        prompt_text = "Alex paid ₹1,200 for dinner. Alex should pay 50%, Alice 25%, and Bob 25%. Exclude Carol."
        # Inject prompt into textarea
        await client.evaluate(f"""
            const ta = document.querySelector('textarea');
            if (ta) {{
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                nativeSetter.call(ta, {json.dumps(prompt_text)});
                ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        """)
        await asyncio.sleep(0.5)
        await client.capture("06_add_expense_ai_prompt.png")

        print("\n--- 7. Add Expense Populated Allocation Desktop ---")
        # Click "Interpret & Fill" button
        await client.evaluate("""
            const btns = Array.from(document.querySelectorAll('button'));
            const interpretBtn = btns.find(b => b.textContent.includes('Interpret & Fill'));
            if (interpretBtn) interpretBtn.click();
        """)
        # Wait for AI result
        for _ in range(30):
            await asyncio.sleep(1)
            has_result = await client.evaluate("Boolean(document.querySelector('.MuiAlert-standardWarning, .MuiPaper-root')) && Array.from(document.querySelectorAll('button')).some(b => b.textContent.includes('Interpret & Fill'))")
            is_thinking = await client.evaluate("Array.from(document.querySelectorAll('button')).some(b => b.textContent.includes('Thinking...'))")
            if not is_thinking:
                break
        await asyncio.sleep(1.5)
        await client.evaluate("window.scrollTo(0, 350)")
        await asyncio.sleep(0.5)
        await client.capture("07_add_expense_interpreted_desktop.png")

        print("\n--- 8. Add Expense Populated Allocation Mobile ---")
        await client.set_viewport(375, 812, is_mobile=True)
        await asyncio.sleep(0.5)
        await client.evaluate("window.scrollTo(0, 400)")
        await asyncio.sleep(0.5)
        await client.capture("08_add_expense_interpreted_mobile.png")

        # -------------------------------------------------------------
        # 9 - 14. Receipt Scanner Complete Workflow
        # -------------------------------------------------------------
        print("\n--- 9. Receipt Scanner File Selected & Preview ---")
        await client.set_viewport(1280, 800, is_mobile=False)
        await client.navigate_and_wait(f"{BASE_URL}/receipt-scanner?groupId=13")

        # Select sample_receipt.png via CDP DOM.setFileInputFiles
        doc = await client.send("DOM.getDocument")
        node = await client.send("DOM.querySelector", {
            "nodeId": doc["root"]["nodeId"],
            "selector": "#receipt-file-input"
        })
        receipt_path = os.path.abspath("sample_receipt.png")
        await client.send("DOM.setFileInputFiles", {
            "nodeId": node["nodeId"],
            "files": [receipt_path]
        })
        await client.evaluate("""
            const input = document.getElementById('receipt-file-input');
            input.dispatchEvent(new Event('change', { bubbles: true }));
        """)
        await asyncio.sleep(1.5)
        await client.capture("09_receipt_upload_preview.png")

        print("\n--- 10. Receipt Processing State ---")
        # Click Start AI Extraction
        await client.evaluate("""
            const btns = Array.from(document.querySelectorAll('button'));
            const scanBtn = btns.find(b => b.textContent.includes('Start AI Extraction'));
            if (scanBtn) scanBtn.click();
        """)
        await asyncio.sleep(0.4)
        await client.capture("10_receipt_extracting_state.png")

        # Wait for extraction to complete (up to 45 seconds for Ollama)
        print("Waiting for AI extraction...")
        for _ in range(45):
            await asyncio.sleep(1)
            stage_done = await client.evaluate("Boolean(document.querySelector('table')) || Array.from(document.querySelectorAll('h6')).some(h => h.textContent.includes('Extracted Receipt Details'))")
            if stage_done:
                break
        await asyncio.sleep(2)

        print("\n--- 11. Receipt Review Totals ---")
        await client.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)
        await client.capture("11_receipt_review_totals.png")

        print("\n--- 12. Receipt Review Items ---")
        await client.evaluate("window.scrollTo(0, 300)")
        await asyncio.sleep(0.5)
        await client.capture("12_receipt_review_items.png")

        print("\n--- 13. Receipt Reconciled Status ---")
        await client.evaluate("window.scrollTo(0, 100)")
        await asyncio.sleep(0.5)
        await client.capture("13_receipt_reconciled_status.png")

        print("\n--- 14. Mobile Receipt Review ---")
        await client.set_viewport(375, 812, is_mobile=True)
        await asyncio.sleep(0.5)
        await client.evaluate("window.scrollTo(0, 150)")
        await asyncio.sleep(0.5)
        await client.capture("14_receipt_review_mobile.png")

        # -------------------------------------------------------------
        # 15 & 16. Analytics Baseline Labels (Desktop & Mobile)
        # -------------------------------------------------------------
        print("\n--- 15. Analytics Desktop Baseline ---")
        await client.set_viewport(1280, 800, is_mobile=False)
        await client.navigate_and_wait(f"{BASE_URL}/analytics?groupId=13")
        await client.evaluate("window.scrollTo(0, 450)")
        await asyncio.sleep(0.5)
        await client.capture("15_analytics_desktop_baseline.png")

        print("\n--- 16. Analytics Mobile Baseline ---")
        await client.set_viewport(375, 812, is_mobile=True)
        await client.navigate_and_wait(f"{BASE_URL}/analytics?groupId=13")
        await client.evaluate("window.scrollTo(0, 600)")
        await asyncio.sleep(0.5)
        await client.capture("16_analytics_mobile_baseline.png")

        print("\n=== ALL 16 VERIFICATION SCREENSHOTS CAPTURED SUCCESSFULLY ===")

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())
