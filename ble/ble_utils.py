import asyncio
from bleak import BleakClient, discover

BASE_UUID = "00000000-0000-1000-8000-00805f9b34fb"

def uuid16_to_uuid(uuid16):
    """Convert a 16-bit UUID to the 128-bit UUID format using the base uuid"""
    return f"0000{uuid16:04x}{BASE_UUID[8:]}"


#+                          DEVICE DISCOVERY                            +#
async def scan_for_mydevice(device_name, timeout=3):
    """Scan for specified BLE device, return MAC address if found"""
    mydevice_mac_address = None # default return value
    devices = await discover(timeout=timeout) # Scan for devices
    for device in devices:
        # look for specified device
        if device.name and device_name in device.name:
            mydevice_mac_address = device
            break  # Stop scanning after finding the device
    
    # return the device if found, otherwise return None
    return mydevice_mac_address

async def scan_for_multiple_devices(keyword, timeout=3):
    """Scan for multiple BLE devices, return list of devices if found"""
    clients = {}
    device_list = []
    devices = await discover(timeout=timeout) # Scan for devices
    for device in devices:
        # look for specified device
        if device.name and keyword in device.name: # if device name includes keyword, add to device_list
            device_list.append(device)

    if device_list: # if device_list is not empty
        print(f"\nFound {len(device_list)} devices named {keyword}.\n")
        for device in device_list:
            print(f"Found {device.name} with MAC address: {device.address}")
            # create client using device's MAC address
            client = BleakClient(device.address)

            # add client to clients dict
            clients[device.name] = {}
            clients[device.name]["client"] = client # client object
            clients[device.name]["score"] = 0 # player's score
            clients[device.name]["address"] = device.address # client's address
            clients[device.name]["buzzed"] = False
    
    # return the client_dict if found, otherwise return {}
    return clients


#+                      CONNECTION/DISCONNECTION                        +#
async def connect(client):
    """Connect to the specified client"""
    print("Connecting...")
    await client.connect()
    print("Connected!")

async def connect_multiple(clients): #? updated with dict
    """Connect to multiple clients"""
    print("\nConnecting to all clients...")
    for client in list(clients.keys()):
        print(f"Connecting to {client} {clients[client]['address']}...")
        await clients[client]["client"].connect()
        print(f"Connected to {client} {clients[client]['address']}!")
    print("Connected to all devices!\n")

async def disconnect(client):
    """Disconnect from the specified client"""
    print("Disconnecting...")
    await client.disconnect()
    print("Disconnected!")

async def disconnect_multiple(clients): #? updated with dict
    """Disconnect from multiple clients"""
    print("Disconnecting from all clients...")
    for client in list(clients.keys()):
        print(f"Disconnecting from {client} {clients[client]['address']}...")
        await clients[client]['client'].disconnect()
        print(f"Disconnected from {client} {clients[client]['address']}!")
    print("Disconnected from all devices!")
        

#+                  CHARACTERISTIC/SERVICE DISCOVERY                    +#
async def discover_characteristic_uuid(client, char_name):
    """Discover the UUID of a characteristic with the specified name"""
    try:
        # create a list of clients services
        services = client.services
        for service in services:
            # create a list of characteristics for each service
            ch = service.characteristics
            for c in ch:
                # check if the characteristic name is in the description
                if char_name in c.description:
                    return c.uuid
    except Exception as e:
        print(f"Connection or communication error: {e}")

async def scan_services(client):
    """Discover the UUID of a characteristic with the specified name"""
    try:
        # create a list of clients services
        services = client.services
        for service in services:
            print(f"Service: {service}")
            # create and print a list of characteristics for each service
            ch = service.characteristics
            print("Characteristics: ")
            for c in ch:
                print(c)
            print("\n\n")
    except Exception as e:
        print(f"Connection or communication error: {e}")

async def scan_specific_service(client, service_uuid):
    """print the characteristics of a specific service"""
    try:
        # create a list of clients services
        services = client.services
        for service in services:
            # check if the service uuid matches the specified uuid
            if service.uuid == service_uuid:
                print(f"Service: {service}")
                # create a list of characteristics for each service
                ch = service.characteristics
                # handles = []
                print("Characteristics: ")
                for c in ch:
                    print(c)
                    # handles.append(c.handle)
                print("\n\n")
                # return handles
            else:
                pass
        print("service not found")
        return []
    except Exception as e:
        print(f"Connection or communication error: {e}")

async def send_message(client, uuid, message):
    """Send a message to the specified client"""
    await client.write_gatt_char(uuid, message)

async def receive_message(client, uuid):
    """Receive a message from the specified client"""
    return await client.read_gatt_char(uuid)


#+                  NOTIFICATION LISTENERS/HANDLERS                    +#
async def handle_notification_stream(sender, data):
    """Handle a notification stream, display received notification data"""
    sender_name = str(sender)[-7:] # parse the sender name from sender object
    print(f"Received notification from {sender_name}: {data.decode('utf-8')}")

async def handle_notification_single(sender, data):
    """Handle a single notification, kill stream after receiving notification"""
    sender_name = str(sender)[-7:] # parse the sender name from sender object
    print(f"Received notification from {sender_name}: {data.decode('utf-8')}")
    await handle_notification_single.queue.put(sender_name)  # Put the value in the queue
    for task in asyncio.all_tasks():
        task.cancel()

async def start_notification_listener(client, characteristic_uuid):
    """Start a notification listener for the specified client and characteristic"""
    try:
        await client.start_notify(characteristic_uuid, handler=handle_notification_stream)
        print("Notification listener started. Waiting for notifications...")
        while True:
            try:
                await asyncio.sleep(1)  # Keep the event loop running
            except asyncio.CancelledError:
                break
    except Exception as e:
        print(f"Error: {e}")

async def start_multiple_notification_listener(clients, characteristic_uuid, queue, handler=handle_notification_stream):
    """Start a notification listener for multiple clients and a characteristic"""
    try:
        handler.queue = queue
        for client in clients:
            await clients[client]['client'].start_notify(characteristic_uuid, handler)
        print("Notification listener started. Waiting for notifications...")
        while True:
            try:
                await asyncio.sleep(1)  # Keep the event loop running
            except asyncio.CancelledError:
                break
    except Exception as e:
        print(f"Error: {e}")


#+                  INDICATION LISTENERS/HANDLERS                    +#
async def handle_indication_stream(sender, data):
    """Handle an indication stream, display received indication data"""
    sender_name = str(sender)[-7:] # parse the sender name from sender object
    print(f"Received indication from {sender_name}: {data.decode('utf-8')}")

async def handle_indication_single(sender, data):
    """Handle a single indication, kill stream after receiving indication"""
    sender_name = str(sender)[-7:] # parse the sender name from sender object
    verbose = False#await handle_indication_single.queue.get()
    if verbose:
        print(f"Received indication from {sender_name}: {data.decode('utf-8')}")
    await handle_indication_single.queue.put(sender_name)  # Put the value in the queue
    for task in asyncio.all_tasks():
        task.cancel()

async def start_indication_listener(client, char_uuid, queue, handler=handle_indication_stream):
    """Start an indication listener for the specified client and characteristic"""
    try:
        handler.queue = queue # set the queue for the handler
        await client.start_notify(char_uuid, handler, indicate=True) # start the indication listener
        print(f"Indication listener started. Waiting for indications...")
        while True:
            try:
                await asyncio.sleep(1)  # Keep the event loop running
            except asyncio.CancelledError:
                break
    except Exception as e:
        print(f"Error: {e}")

async def start_multiple_indication_listener(clients, char_uuid, queue, verbose=False, handler=handle_indication_stream):
    """start an indication listener for multiple clients and a characteristic"""
    try:
        handler.queue = queue # set the queue for the handler
        # await queue.put(verbose)
        for client in clients:
            if clients[client]['buzzed'] == False: # only start the indication listener if the client hasn't buzzed in yet
                await clients[client]['client'].start_notify(char_uuid, handler, indicate=True) # start the indication listener for each client
        if verbose:
            print(f"Indication listener started. Waiting for indications...")
        while True:
            try:
                await asyncio.sleep(1)  # Keep the event loop running
            except asyncio.CancelledError:
                break
    except Exception as e:
        print(f"Error: {e}")