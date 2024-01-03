import asyncio
from ble_utils import *
from bleak import BleakClient, discover

LB_READ_UUID = 0X0001
LB_WRITE_UUID = 0X0002
BUZZ_UUID = 0x0003
SCORE_UUID = 0x0004

async def main():

    queue = asyncio.Queue()
    mydevice_name = "Player"

    # # Example Scan for single device with name mydevice_name
    # mydevice = await scan_for_mydevice(mydevice_name, 1)
    # if mydevice:
    #     print(f"Found {mydevice_name} with MAC address: {mydevice.address}")
    #     # create client using device's MAC address
    #     client = BleakClient(mydevice.address)
    # else:
    #     print(f"No device named {mydevice_name} found.")
    #     return 
    
    # Example Scan for multiple devices with name mydevice_name
    devices = await scan_for_multiple_devices(mydevice_name, 1)
    clients = []
    client_info = {}
    if devices:
        print(f"Found {len(devices)} devices named {mydevice_name}.")
        for device in devices:
            print(f"Found {device.name} with MAC address: {device.address}")
            # create client using device's MAC address
            client = BleakClient(device.address)
            clients.append([client, device.name])
            client_info[device.name] = [client]
    else:
        print(f"No device named {mydevice_name} found.")
        return

    #await connect(client) # Example connect to single client
    await connect_multiple(clients) # Example connect to multiple clients

    # # Example of scanning a service for all clients
    # for client in clients:
    #     await scan_specific_service(client[0], uuid16_to_uuid(0x1111))


    # # Example of scanning all services and a specific service
    # await scan_services(client)
    # await scan_specific_service(client, uuid16_to_uuid(0x1111))


    # # Example sending a message to the device
    # # First discover the UUID of the characteristic to write to
    # characteristic_name = "lightblue write"
    # characteristic_uuid = await discover_characteristic_uuid(client, characteristic_name)
    # message_to_send = b"Hello from computer!"  # Convert string to bytes
    # await send_message(client, characteristic_uuid, message_to_send)


    # # Example receiving a message from the devicew
    # # First discover the UUID of the characteristic to read from
    # characteristic_name = "lightblue read"
    # uuid = await discover_characteristic_uuid(client, characteristic_name)
    # print(f"UUID: {uuid}")
    # received_message = await receive_message(client, uuid)
    # print(f"Received message from {mydevice_name}: {received_message.decode()}")


    # # Example of indication listener, both single and multiple
    # await start_indication_listener(client, uuid16_to_uuid(BUZZ_UUID), queue)
    # await start_multiple_indication_listener(clients, uuid16_to_uuid(BUZZ_UUID), queue)


    # await disconnect(client)
    await disconnect_multiple(clients)

# Run the main function
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
