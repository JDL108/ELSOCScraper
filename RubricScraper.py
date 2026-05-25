import json
import sys
import time
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests

# =============================================
# CONFIGURATION — EDIT THESE
# =============================================
EVENT_ID = "64539"
# EVENT_ID = "64563"
TICKET_TYPE_ID = "2879147"
TICKETS_WANTED = 2
POLL_INTERVAL = 2

# Run this in your browser console and paste the result below:
# JSON.parse(localStorage.jStorage).sessionid
SESSION_ID = "444a27b4-2b64-4508-a961-c62bc36b8e1c"
# =============================================

API_URL = "https://api.hellorubric.com/"

HEADERS = {
    "accept": "*/*",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://campus.hellorubric.com",
    "referer": "https://campus.hellorubric.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "dnt": "1",
}


def ts():
    return int(datetime.now().timestamp() * 1000)


def post(session, details, endpoint):
    payload = {"details": json.dumps(details), "endpoint": endpoint}
    r = session.post(API_URL, data=payload, timeout=10)
    return r.json()


def check_availability(session):
    return post(
        session,
        {
            "eventId": EVENT_ID,
            "currentUrl": f"https://campus.hellorubric.com/?eid={EVENT_ID}",
            "device": "web_portal",
            "version": 4,
            "timestamp": ts(),
        },
        "https://appserver.getqpay.com:9090/AppServerSwapnil/event/details",
    )


def secure_ticket(session):
    return post(
        session,
        {
            "waiting": False,
            "tickettypesChosen": [TICKET_TYPE_ID] * TICKETS_WANTED,
            "eventId": EVENT_ID,
            "currentUrl": f"https://campus.hellorubric.com/?eid={EVENT_ID}",
            "device": "web_portal",
            "version": 4,
            "timestamp": ts(),
        },
        "https://appserver.getqpay.com:9090/AppServerSwapnil/event/tickets/secure",
    )


def verify_cart(session, flow_uid):
    now = ts()
    return post(
        session,
        {
            "cartItems": [{"created": now, "type": "ticket", "flowUid": flow_uid}],
            "sessionid": SESSION_ID,
            "currentUrl": f"https://campus.hellorubric.com/?eid={EVENT_ID}",
            "device": "web_portal",
            "version": 4,
            "timestamp": now,
        },
        "verifyUnifiedCart",
    )


def get_recommendations(session, flow_uid, ruuid):
    return post(
        session,
        {
            "cartItems": [{"created": ts(), "type": "ticket", "flowUid": flow_uid}],
            "ruuid": ruuid,
            "currentUrl": f"https://campus.hellorubric.com/?eid={EVENT_ID}",
            "device": "web_portal",
            "version": 4,
            "timestamp": ts(),
        },
        "getCartRecommendations",
    )


def inject_cart_to_browser(flow_uid):
    """Launches browser, sets local storage natively, and refreshes."""
    print("🌐 Launching browser via Selenium...")

    chrome_options = Options()
    # Keeps the browser open after the python script finishes execution
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)
    target_url = f"https://campus.hellorubric.com/?eid={EVENT_ID}"

    # 1. Navigate to the page first (Required before you can interact with localStorage)
    driver.get(target_url)

    # 2. Structure the data exactly how jStorage expects it
    now = ts()
    cart_data = [{"created": now, "type": "ticket", "flowUid": flow_uid}]

    # 3. Construct the session object inside jStorage format
    jstorage_payload = {"sessionid": SESSION_ID, "cartItems": cart_data}

    # 4. Use execute_script to write directly into localStorage
    print("⚡ Injecting cart token into localStorage...")
    script = f"localStorage.setItem('jStorage', JSON.stringify({json.dumps(jstorage_payload)}));"
    driver.execute_script(script)

    # 5. Refresh page to reflect the active cart UI instantly
    driver.refresh()
    print("🎉 Page refreshed! Your cart should now be active.")


def attempt_checkout(session):
    print("🎯 Attempting checkout...")

    ticket_resp = secure_ticket(session)
    if not ticket_resp.get("success"):
        print(f"   ❌ Failed to secure ticket: {ticket_resp}")
        return False

    flow_uid = ticket_resp.get("flowUid")
    print(f"   ... Got flowUid: {flow_uid}")

    cart_resp = verify_cart(session, flow_uid)
    if not cart_resp.get("success"):
        print(f"   ❌ Cart verification failed: {cart_resp}")
        return False

    quantity = cart_resp.get("cartArray", [{}])[0].get("quantityRequested", "?")
    print(f"   ... Cart verified — {quantity} tickets secured for 10 mins")

    ruuid = str(uuid.uuid4())
    get_recommendations(session, flow_uid, ruuid)

    # Trigger automated browser injection
    try:
        inject_cart_to_browser(flow_uid)
        return True
    except Exception as e:
        print(f"   ❌ Error injecting into browser: {e}")
        return False


def monitor():
    if SESSION_ID == "paste-your-sessionid-here":
        print("❌ ERROR: You need to set your SESSION_ID first!")
        sys.exit(1)

    print("==================================================")
    print("🚀 TICKET SNIPER ACTIVATED (AUTO-BROWSER)")
    print(f"📡 Event ID: {EVENT_ID}")
    print(f"🎟️  Tickets wanted: {TICKETS_WANTED}")
    print(f"⏱️  Polling every {POLL_INTERVAL}s")
    print("==================================================")

    with requests.Session() as session:
        session.headers.update(HEADERS)

        while True:
            try:
                data = check_availability(session)

                if not data.get("success"):
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️  API error")
                    time.sleep(POLL_INTERVAL)
                    continue

                event_details = data.get("eventDetails", {})
                event_name = event_details.get("eventName", f"Event #{EVENT_ID}")
                status = data.get("ticketStatus", "Unknown")
                remaining = data.get("selectNumberOfTickets", 0)
                timestamp = time.strftime("%H:%M:%S")

                if status == "Available":
                    print(
                        f"[{timestamp}] ✅ AVAILABLE — {event_name} | Remaining: {remaining}"
                    )
                    success = attempt_checkout(session)
                    if success:
                        print("🏁 Process completed successfully!")
                        sys.exit(0)
                    else:
                        print("❌ Checkout attempt failed, retrying...")
                else:
                    print(f"[{timestamp}] ❌ {status} — {event_name}")

            except requests.exceptions.Timeout:
                print("📡 Timed out, retrying...")
            except requests.exceptions.RequestException as e:
                print(f"📡 Network error: {e}")
            except ValueError as e:
                print(f"⚠️  JSON error: {e}")

            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n👋 Monitor deactivated.")
        sys.exit(0)
