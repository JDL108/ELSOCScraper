import requests
import time
import sys
import json
from datetime import datetime

def monitor_ticket_availability(event_id, interval_seconds=60):
    url = "https://api.hellorubric.com/"
    
    headers = {
        "authority": "api.hellorubric.com",
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://campus.hellorubric.com",
        "referer": "https://campus.hellorubric.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "dnt": "1",
    }

    def build_payload():
        return {
            "details": json.dumps({
                "eventId": event_id,
                "currentUrl": f"https://campus.hellorubric.com/?eid={event_id}",
                "device": "web_portal",
                "version": 4,
                "timestamp": int(datetime.now().timestamp() * 1000)  # fresh timestamp each call
            }),
            "endpoint": "https://appserver.getqpay.com:9090/AppServerSwapnil/event/details"
        }

    print("==================================================")
    print(f"🚀 TICKET MONITOR ACTIVATED")
    print(f"📡 Event ID: {event_id}")
    print(f"⏱️  Polling every {interval_seconds}s")
    print("==================================================")

    with requests.Session() as session:
        session.headers.update(headers)

        while True:
            try:
                response = session.post(url, data=build_payload(), timeout=10)

                if "text/html" in response.headers.get("Content-Type", ""):
                    print("⚠️  Got HTML back — unexpected response")
                    time.sleep(interval_seconds)
                    continue

                if response.status_code == 200:
                    data = response.json()

                    if not data.get("success"):
                        print(f"⚠️  API returned success=false: {data}")
                        time.sleep(interval_seconds)
                        continue

                    event_details = data.get("eventDetails", {})
                    event_name = event_details.get("eventName", f"Event #{event_id}")
                    event_time = event_details.get("eventTime", "Unknown time")
                    status = data.get("ticketStatus", "Unknown")
                    max_purchase = data.get("selectNumberOfTickets", 0)

                    timestamp = time.strftime("%H:%M:%S")

                    if status == "Available":
                        print(f"[{timestamp}] ✅ AVAILABLE — {event_name} ({event_time}) | Max tickets: {max_purchase}")
                    elif status in ["Sold Out", "Unavailable"]:
                        print(f"[{timestamp}] ❌ {status} — {event_name} ({event_time})")
                    else:
                        print(f"[{timestamp}] ℹ️  Status: '{status}' — {event_name}")

                else:
                    print(f"⚠️  HTTP {response.status_code}: {response.text[:200]}")

            except requests.exceptions.Timeout:
                print("📡 Timed out, retrying next cycle...")
            except requests.exceptions.RequestException as e:
                print(f"📡 Network error: {e}")
            except ValueError:
                print(f"⚠️  Non-JSON response: {response.text[:200]}")

            time.sleep(interval_seconds)


if __name__ == "__main__":
    TARGET_EVENT_ID = "64539"
    POLL_INTERVAL = 60

    try:
        monitor_ticket_availability(TARGET_EVENT_ID, interval_seconds=POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n👋 Monitor deactivated.")
        sys.exit(0)
