import asyncio
import warnings
from ble_utils import *

LB_READ_UUID = 0X0001
LB_WRITE_UUID = 0X0002
BUZZ_UUID = 0x0003
SCORE_UUID = 0x0004

SERVICE_UUID = 0x1111

async def buzzer_listener(clients, uuid, queue, score_val=200, indicate=True):
    """Create a buzzer listener with conditional logic to open/close stream"""

    if not indicate: # use notify
        while True:
            # open listener
            await start_multiple_notification_listener(clients, uuid, queue, handle_notification_single)
            
            # close listener after receiving notification
            for client in clients:
                if clients[client]['buzzed'] == False: # if client has not buzzed in
                    await clients[client]['client'].stop_notify(uuid)

            # prompt user
            buzzed_in = await queue.get()  # Get the value from the queue
            ans = input("right or wrong? (r/w)\n")

            if ans == 'w': # reopen stream if answer incorrect
                await send_message(clients[buzzed_in]['client'], uuid16_to_uuid(SCORE_UUID), b"incorrect")
                clients[buzzed_in]['buzzed'] = True
                print("answer wrong, restarting stream")
            elif ans == 'r': # end stream if answer correct
                await send_message(clients[buzzed_in]['client'], uuid16_to_uuid(SCORE_UUID), b"correct")
                print("answer right, ending stream")
                break

    else: # use indicate
        while True:
            # open listener
            await start_multiple_indication_listener(clients, uuid, queue, handle_indication_single)
            
            # close listener after receiving indication
            for client in clients:
                if clients[client]['buzzed'] == False:
                    await clients[client]['client'].stop_notify(uuid)

            # prompt user
            buzzed_in = await queue.get()  # Get the value from the queue
            print(f"{buzzed_in} buzzed in")
            ans = input("right or wrong? (r/w)\n")
            if ans == 'w': # reopen stream if answer incorrect
                await send_message(clients[buzzed_in]['client'], uuid16_to_uuid(SCORE_UUID), b"incorrect")
                clients[buzzed_in]['buzzed'] = True
                print("answer wrong, restarting stream")
            elif ans == 'r': # end stream if answer correct
                await send_message(clients[buzzed_in]['client'], uuid16_to_uuid(SCORE_UUID), b"correct")
                print("answer right, ending stream")
                break

async def main():
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    queue = asyncio.Queue()
    mydevice_name = "Player"
    
    # Scan for multiple devices with name mydevice_name
    clients = await scan_for_multiple_devices(mydevice_name, 1)
    if not clients: # check if any devices were found
        print("No devices found.")
        return

    #await connect(client)
    # await connect_multiple(clients)

    # using my buzzer listener
    # await buzzer_listener(clients, uuid16_to_uuid(BUZZ_UUID), queue)

    # await disconnect(client)
    await disconnect_multiple(clients)

# Run the main function
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
