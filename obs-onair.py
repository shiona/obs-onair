import obspython as obs
import socket
import re

sock = None


def script_description():
	return "Communicate streaming/recoding state changes to a light"


def script_properties():
	props = obs.obs_properties_create()
	obs.obs_properties_add_text(props, "host", "Hostname or IP", obs.OBS_TEXT_DEFAULT)
	obs.obs_properties_add_int(props, "port", "Light TCP port", 0, 2**16-1, 1)
	return props


def script_defaults(props):
	obs.obs_data_set_default_string(props, "host", "on_air_light")
	obs.obs_data_set_default_int(props, "ip", 7777)


def script_load(props):
	ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
	host = obs.obs_data_get_string(props, "host")
	port = obs.obs_data_get_int(props, "port")
	ip = host if ip_pattern.match(host) else try_get_ip(host)

	if ip:
		obs.obs_frontend_add_event_callback(create_event_handler(ip, port))
	else:
		print(f"Not a legal ip or host: \"{host}\"")


def try_get_ip(host):
	try:
		return socket.gethostbyname(host)
	except:
		return None


def script_unload():
	global sock
	if sock:
		sock.shutdown()
		sock.close()


def create_event_handler(ip, port):
	print(f"[?] Trying to connect to {ip}:{port}")
	global sock
	try:
		sock = socket.create_connection((ip, port), timeout=2)
	except socket.timeout:
		print("[-] Could not connect")
		return

	print("[+] Connected")

	def handle_event(event):
		# No need for "OBS on" / "OBS off" messages. TCP connection
		# state is enough information.
		LIVE_ON = [ obs.OBS_FRONTEND_EVENT_STREAMING_STARTED
			  , obs.OBS_FRONTEND_EVENT_RECORDING_STARTED
			  , obs.OBS_FRONTEND_EVENT_RECORDING_UNPAUSED
			  ]
		LIVE_OFF = [ obs.OBS_FRONTEND_EVENT_STREAMING_STOPPED
			   , obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED
			   , obs.OBS_FRONTEND_EVENT_RECORDING_PAUSED
			   ]

		print(event)
		if event in LIVE_ON:
			sock.sendall(b'\x01')
			print("on")
		elif event in LIVE_OFF:
			sock.sendall(b'\x00')
			print("off")

	return handle_event
