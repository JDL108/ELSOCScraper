import requests
import time
import sys
import json
import uuid
from datetime import datetime

# =============================================
# CONFIGURATION — EDIT THESE
# =============================================
EVENT_ID = "64539"
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
    payload = {
        "details": json.dumps(details),
        "endpoint": endpoint
    }
    r = session.post(API_URL, data=payload, timeout=10)
    return r.json()

def check_availability(session):
    return post(session, {
        "eventId": EVENT_ID,
        "currentUrl": f"https://campus.hellorubric.com/?eid={EVENT_ID}",
        "device": "web_portal",
        "version": 4,
        "timestamp": ts()
    }, "https://appserver.getqpay.com:9090/AppServerSwapnil/event/details")

def secure_ticket(session):
    return post(session, {
        "waiting": False,
        "tickettypesChosen": [TICKET_TYPE_ID] * TICKETS_WANTED,
        "eventId": EVENT_ID,
        "currentUrl": f"https://campus.hellorubric.com/?eid={EVENT_ID}",
        "device": "web_portal",
        "version": 4,
        "timestamp": ts()
    }, "https://appserver.getqpay.com:9090/AppServerSwapnil/event/tickets/secure")

def verify_cart(session, flow_uid):
    now = ts()
    return post(session, {
        "cartItems": [{"created": now, "type": "ticket", "flowUid": flow_uid}],
        "sessionid": SESSION_ID,
        "currentUrl": f"https://campus.hellorubric.com/?eid={EVENT_ID}",
        "device": "web_portal",
        "version": 4,
        "timestamp": now
    }, "verifyUnifiedCart")

def get_recommendations(session, flow_uid, ruuid):
    return post(session, {
        "cartItems": [{"created": ts(), "type": "ticket", "flowUid": flow_uid}],
        "ruuid": ruuid,
        "currentUrl": f"https://campus.hellorubric.com/?eid={EVENT_ID}",
        "device": "web_portal",
        "version": 4,
        "timestamp": ts()
    }, "getCartRecommendations")

def attempt_checkout(session):
    print("🎯 Attempting checkout...")

    # Step 1 — secure the tickets
    ticket_resp = secure_ticket(session)
    print(f"   tickets/secure response: {ticket_resp}")

    if not ticket_resp.get("success"):
        print("   ❌ Failed to secure ticket")
        return False

    flow_uid = ticket_resp.get("flowUid")
    print(f"   ✅ Got flowUid: {flow_uid}")

    # Step 2 — verify cart using your real browser session
    cart_resp = verify_cart(session, flow_uid)
    print(f"   verifyUnifiedCart response: {cart_resp}")

    if not cart_resp.get("success"):
        print("   ❌ Cart verification failed")
        return False

    quantity = cart_resp.get("cartArray", [{}])[0].get("quantityRequested", "?")
    print(f"   ✅ Cart verified — {quantity} tickets secured")

    # Step 3 — recommendations (fires in background, needed to complete flow)
    ruuid = str(uuid.uuid4())
    rec_resp = get_recommendations(session, flow_uid, ruuid)
    print(f"   getCartRecommendations: {'✅' if rec_resp.get('success') else '❌'}")

    print(f"\n{'='*50}")
    print(f"🛒 TICKETS SECURED — OPEN YOUR BROWSER NOW:")
    print(f"   https://campus.hellorubric.com/?eid={EVENT_ID}")
    print(f"{'='*50}")

    return True

def monitor():
    if SESSION_ID == "paste-your-sessionid-here":
        print("❌ ERROR: You need to set your SESSION_ID first!")
        print("   Run this in your browser console:")
        print("   JSON.parse(localStorage.jStorage).sessionid")
        sys.exit(1)

    print("==================================================")
    print(f"🚀 TICKET SNIPER ACTIVATED")
    print(f"📡 Event ID: {EVENT_ID}")
    print(f"🎟️  Tickets wanted: {TICKETS_WANTED}")
    print(f"⏱️  Polling every {POLL_INTERVAL}s")
    print(f"🔑 Session ID: {SESSION_ID[:8]}...")
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
                    print(f"[{timestamp}] ✅ AVAILABLE — {event_name} | Remaining: {remaining}")
                    success = attempt_checkout(session)
                    if success:
                        print("\n✅ Done! Your cart is loaded. Complete payment in your browser.")
                        sys.exit(0)
                    else:
                        print("❌ Checkout attempt failed, retrying next poll...")
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

# paste id and paste this in console after script:

# // Replace these with the values from your script output
# var flowUid = "633b4a57-4b98-46d7-a635-f4bbb61fee78";
# var sessionId = "444a27b4-2b64-4508-a961-c62bc36b8e1c";

# var storage = JSON.parse(localStorage.jStorage);
# storage.cartItems = [{"created": Date.now(), "type": "ticket", "flowUid": flowUid}];
# storage.sessionid = sessionId;
# localStorage.jStorage = JSON.stringify(storage);

# // Then reload the page
# location.reload();
