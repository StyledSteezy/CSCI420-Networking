import asyncio
import socket
import sys
import ast
from subprocess import call

# returns a list of substrings of desired length
def chunkstring(string, length):
    return [string[0+i:length+i] for i in range(0, len(string), length)]

# Takes a big message and a destination and sends to destination via many smaller packets
def sendMsg(msg, destination):
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    packets_ls = chunkstring(msg, 600)
    for i in range(len(packets_ls)):
        msgToSend = str((i,len(packets_ls),packets_ls[i]))  # Each message is a tuple (part #, total parts, actual message)
        bytesToSend         = str.encode(msgToSend)
        UDPServerSocket.sendto(bytesToSend, destination)


async def delay():
    await asyncio.sleep(30)

class ChannelProtocol(asyncio.DatagramProtocol):
    def __init__(self, t):
        self.t = t
    def datagram_received(self, data, addr):
        self.t.put_nowait((addr,data))

async def main():
    loop = asyncio.get_running_loop()

    chan = asyncio.Queue(0)
    await loop.create_datagram_endpoint(
        lambda: ChannelProtocol(chan),
        local_addr=('0.0.0.0', 9056))
    
    print("UDP server up and listening")

    t = asyncio.create_task(chan.get())  # Listens for messages from client
    d = asyncio.create_task(delay())     # Counts off 30 seconds. Not necessary for functioning

    msgDict = {}  # Mapping from packet number to string of packet content. When complete will contain entire message
                  # from the client
    sendBackPpm = False  # Tells the server when to send ppm back to client
    while True:

        if sendBackPpm == True:
            ppmFile = open("out.ppm", "r")
            msgFromServer = ppmFile.read()
            ppmFile.close()
            clientAddressPort   = (clientIp, 8056)
            sendMsg(msgFromServer, clientAddressPort)  # Having done raytracing, sends result back to client
            sendBackPpm = False


        done, pending = await asyncio.wait([t,d], return_when=asyncio.FIRST_COMPLETED)

        if d in done:
            print(f"30 seconds has passed.")
            d = asyncio.create_task(delay())

        if t in done:
            ip,bytes = t.result()
            clientMsg = bytes.decode('utf-8')
            clientIp = ip[0]

            if clientMsg == "Resend Message":  # Client did not receive entire message. Send again
                ppmFile = open("out.ppm", "r")
                msgFromServer = ppmFile.read()
                ppmFile.close()
                clientAddressPort   = (clientIp, 8056)
                sendMsg(msgFromServer, clientAddressPort)

            elif clientMsg == "End Server":  # Client told us the job is complete! We can stop now
                break

            elif clientMsg[0] == "P":  # A message starting with P indicates the client is telling us which piece to work
                                        # on, as well as how many total pieces
                msgList = clientMsg.split(",")
                piece = msgList[1]
                num_pieces = msgList[2]
                print("This server will work on piece " + str(piece) + " out of " + str(num_pieces))
            else:  # At this point we are receiving scene data, which is broken into packets. Each packet is a tuple.
                   # (Part #, Total parts, Actual message)

                #print(clientMsg)
                msgTup = ast.literal_eval(clientMsg)
                if isinstance(msgTup, tuple) == False:
                    print("Error: Message is not a tuple")
                elif len(msgTup) != 3:
                    print("Error: Message is not the correct length")
                elif isinstance(msgTup[0], int) == False or isinstance(msgTup[1], int) == False:
                    print("Error: Message does not contain valid values")
                current_part = msgTup[0]
                total_parts = msgTup[1]
                msg = msgTup[2]

                msgDict[current_part] = msg   
            
                if len(msgDict) == total_parts:  # We have recieved all parts of the message. Order and write to scene file
                    outputFile = open("output.scene", "w")
                    for k in msgDict:
                        outputFile.write(msgDict[k])
                    outputFile.close()

                    # Actually do raytracing
                    call(["python", "raytracer-numpy.py", "output.scene", "out.ppm", str(piece), str(num_pieces)])
                    sendBackPpm = True  # Now that we have done raytracing, we can tell client what we made

            t = asyncio.create_task(chan.get())


asyncio.run(main())
