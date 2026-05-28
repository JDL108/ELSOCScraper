import json
import sys
import time
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests

# =========================================================================
# CONFIGURATION — EDIT THESE THREE VALUES
# =========================================================================
# Testing values:
# EVENT_ID = "64539"            # ELSOC grilled cheese (should succeed)
# EVENT_ID = "64542"            # ELSOC beer and pizza (should succeed)
# EVENT_ID = "64563"            # Random event - presale (should fail)
EVENT_ID = "63678"              # ELSOC cruise - wallahi
TICKETS_WANTED = 2
POLL_INTERVAL = 0.1  # Time in seconds between API availability checks

# Run this in your browser console on the event page and paste the result below:
# JSON.parse(localStorage.jStorage).sessionid
SESSION_ID = "paste-your-sessionid-here"
# =========================================================================

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


def secure_ticket(session, ticket_ids_array):
    return post(
        session,
        {
            "waiting": False,
            "tickettypesChosen": ticket_ids_array,
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
    print("🌐 Launching browser via Selenium...")
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)
    target_url = f"https://campus.hellorubric.com/?eid={EVENT_ID}"
    driver.get(target_url)

    now = ts()
    cart_data = [{"created": now, "type": "ticket", "flowUid": flow_uid}]
    jstorage_payload = {"sessionid": SESSION_ID, "cartItems": cart_data}

    print("⚡ Injecting cart token into localStorage...")
    script = f"localStorage.setItem('jStorage', JSON.stringify({json.dumps(jstorage_payload)}));"
    driver.execute_script(script)

    driver.refresh()
    print("🎉 Page refreshed! Your cart should now be active.")


def attempt_checkout(session, ticket_ids_array):
    """
    Attempts to secure a ticket and verify the cart.
    Returns the flow_uid on success, or None on failure.
    Browser injection is intentionally NOT done here — it must be called
    after the requests session is closed to avoid ChromeDriver blocking.
    """
    print(f"🎯 Attempting checkout for ticket IDs: {ticket_ids_array}...")

    ticket_resp = secure_ticket(session, ticket_ids_array)
    if not ticket_resp.get("success"):
        print(f"   ❌ Failed to secure tickets: {ticket_resp}")
        return None

    flow_uid = ticket_resp.get("flowUid")
    print(f"   ... Got flowUid: {flow_uid}")

    cart_resp = verify_cart(session, flow_uid)
    if not cart_resp.get("success"):
        print(f"   ❌ Cart verification failed: {cart_resp}")
        return None

    print("   ... Cart verified successfully! Tickets secured for 10 mins.")
    ruuid = str(uuid.uuid4())
    get_recommendations(session, flow_uid, ruuid)

    return flow_uid


def monitor():
    if SESSION_ID == "paste-your-sessionid-here" or not SESSION_ID:
        print("❌ ERROR: You need to set your SESSION_ID first!")
        sys.exit(1)

    print("==================================================")
    print("🚀 PRECISE SHOTGUN SNIPER ACTIVATED")
    print(f"📡 Event ID: {EVENT_ID}")
    print(f"🎟️  Tickets wanted per tier: {TICKETS_WANTED}")
    print(f"⏱️  Polling every {POLL_INTERVAL}s")
    print("==================================================")

    winning_flow_uid = None

    with requests.Session() as session:
        session.headers.update(HEADERS)

        while True:
            try:
                data = check_availability(session)

                if not data.get("success"):
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️  API error (Event details unretrievable)")
                    time.sleep(POLL_INTERVAL)
                    continue

                event_details = data.get("eventDetails", {})
                event_name = event_details.get("eventName", f"Event #{EVENT_ID}")
                status = data.get("ticketStatus", "Unknown")
                timestamp = time.strftime("%H:%M:%S")

                if status == "Available":
                    print(f"[{timestamp}] ✅ AVAILABLE — {event_name} | Parsing ticketTypeDetails...")

                    ticket_type_details = event_details.get("ticketTypeDetails", [])

                    open_tickets = []
                    for t in ticket_type_details:
                        if t.get("ticketSaleOpen") is False:
                            continue
                        conditions = t.get("conditions", [])
                        if conditions:
                            continue
                        open_tickets.append(t)

                    if open_tickets:
                        unique_type_ids = []
                        for t in open_tickets:
                            type_id = t.get("typeId")
                            if type_id and str(type_id) not in unique_type_ids:
                                unique_type_ids.append(str(type_id))

                        if unique_type_ids:
                            print(f"🔍 Targets identified: {unique_type_ids} — trying each in succession...")
                            for type_id in unique_type_ids:
                                ids_to_buy = [type_id] * TICKETS_WANTED
                                print(f"   → Trying ticket type {type_id}...")
                                flow_uid = attempt_checkout(session, ids_to_buy)
                                if flow_uid:
                                    winning_flow_uid = flow_uid
                                    break  # Exit inner loop — browser opened below after session closes
                                else:
                                    print(f"   ↩ Type {type_id} failed, trying next...")

                            if winning_flow_uid:
                                break  # Exit the while loop to close the requests session cleanly
                            else:
                                print("❌ All ticket types failed, continuing loop...")
                        else:
                            print("⚠️ Ticket structures matched, but 'typeId' values are missing.")
                    else:
                        print("⚠️ Event is open, but no active public tiers found (all options may be locked/closed).")
                else:
                    print(f"[{timestamp}] ❌ {status} — {event_name}")

            except requests.exceptions.Timeout:
                print("📡 Timed out, retrying...")
            except requests.exceptions.RequestException as e:
                print(f"📡 Network error: {e}")
            except ValueError as e:
                print(f"⚠️  JSON error: {e}")

            time.sleep(POLL_INTERVAL)

    # Requests session is now fully closed — safe to launch Chrome
    if winning_flow_uid:
        print("🏁 Ticket secured! Launching browser...")
        try:
            inject_cart_to_browser(winning_flow_uid)
            print("✅ Process completed successfully! Check your browser window.")
        except Exception as e:
            print(f"❌ Error injecting into browser: {e}")
            print(f"   Your flowUid was: {winning_flow_uid}")
            print(f"   You can manually inject it at: https://campus.hellorubric.com/?eid={EVENT_ID}")
    else:
        print("❌ Exited without a winning ticket.")


if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n👋 Monitor deactivated.")
        sys.exit(0)