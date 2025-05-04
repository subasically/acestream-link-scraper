import requests

def send_ntfy_notification(title: str, message: str, topic: str = "basic-server"):
	"""
	Send a notification to the ntfy server.

	Args:
		title (str): The notification title.
		message (str): The notification message.
		topic (str): The ntfy topic (default: "basic-server").
	"""
	url = f"https://ntfy.subasically.me/{topic}"
	headers = {
		"Title": title
	}
	response = requests.post(url, data=message.encode('utf-8'), headers=headers)
	response.raise_for_status()
	return response

# Example usage:
# send_ntfy_notification("Test Title", "This is a test message.")