import socket
import asyncio
import sys
import ast

# Terminal command to copy client.py to clyon directory of d13056:
# scp client.py cslab@d13056:clyon

# Terminal command to copy out.ppm from clyon directory of d13056 to Caleb's Networking Project1 folder:
# scp cslab@d13056:clyon\out.ppm C:\Users\caleb\Documents\Spring_2020\Networking\Project1

serverList = list(map(socket.gethostbyname, ['D13054', 'D13052', 'D13055', 'D09105', 'D09106', 'D09096', 'D09097']))

serverDict = {}  # serverDict maps server ips to tuples with a dictionary of messages recieved from this server and 
                 # a boolean indicating whether all messages have been received
partsDict = {}   # Keeps track of the total number of packets to be received from each server (only used for printing purposes)
combinedDict = {} # Combines the ip to entire string of the message from that server
for ip in serverList:
    serverDict[ip] = ({}, False)
    partsDict[ip] = 0

bufferSize          = 1024

# Clearing ppm files so they don't have to be deleted between each test run
for ip in serverList:
    filename = "out." + ip + ".ppm"
    outputFile = open(filename, "w")
    outputFile.write("")

# returns a list of substrings of desired length
def chunkstring(string, length):
    return [string[0+i:length+i] for i in range(0, len(string), length)]
        

# Takes a big message and a destination and sends to destination via many smaller packets
def sendMsg(msg, destination):
    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    packets_ls = chunkstring(msg, 600)
    for i in range(len(packets_ls)):
        msgToSend = str((i,len(packets_ls),packets_ls[i]))
        bytesToSend         = str.encode(msgToSend)
        UDPClientSocket.sendto(bytesToSend, destination)

# Breaks up the work to be done and sends it to all servers in server list
def sendWork(sList):
    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    for i in range(len(sList)):
        sceneFile = open("default.scene", "r")
        SmsgFromClient   = "S:" + sceneFile.read()  # Scene data
        sceneFile.close()
        PmsgFromClient       = "P," + str(i+1) + "," + str(len(sList))  # Part for server to work on
        serverAddressPort   = (sList[i], 9056)

        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        PbytesToSend         = str.encode(PmsgFromClient)
        UDPClientSocket.sendto(PbytesToSend, serverAddressPort)
        sendMsg(SmsgFromClient, serverAddressPort)

# Shows that the client is waiting on packets from the server
async def delay():
    await asyncio.sleep(30)

# When a packet is dropped request the server to resend the packet
async def request_resend():
    await asyncio.sleep(0.0001)

# prints information regarding the server ip and parts
async def print_stuff():
    await asyncio.sleep(30)

# Once all parts are received servers the final ppm is created and then its ended
async def end():
    await asyncio.sleep(5)


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
        local_addr=('0.0.0.0', 8056))
    
    t = asyncio.create_task(chan.get())
    d = asyncio.create_task(delay())        
    rr = asyncio.create_task(request_resend())
    p = asyncio.create_task(print_stuff())
    e = asyncio.create_task(end())

    sendWork(serverList)

    while True:
        done, pending = await asyncio.wait([t,d, rr, p, e], return_when=asyncio.FIRST_COMPLETED)

        if d in done:
            print(f"30 seconds has passed.")
            d = asyncio.create_task(delay())

        if p in done:
            for ip in serverList:
                if serverDict[ip][1] == False:
                    print("Server ip: ", ip)
                    print("Total Parts:", partsDict[ip])
                    print("Parts Received:",len(serverDict[ip][0]))
                    print()
            p = asyncio.create_task(print_stuff())

        if e in done:
            totally_done = True
            for ip in serverList:
                if serverDict[ip][1] == False:
                    totally_done = False
            if totally_done == True:
                print("Received All Messages From All Servers")
                total_out_list = []
                for ip in serverList:
                    out_string = combinedDict[ip]
                    out_list = out_string.split()
                    if len(total_out_list) == 0:
                        for i in range(len(out_list)):
                            if i in [0,1,2,3]:
                                total_out_list.append(out_list[i])
                            else:    
                                total_out_list.append(int(out_list[i]))
                    else:
                        for i in range(4, len(out_list)):
                            total_out_list[i] += int(out_list[i])

                    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                    bytesToSend         = str.encode("End Server")
                    UDPClientSocket.sendto(bytesToSend, (ip, 9056)) 

                final_out_file = open("out.ppm", "w")
                for elem in total_out_list:
                    final_out_file.write(str(elem) + " ")
                break
            e = asyncio.create_task(end())


        if rr in done:
            for ip in serverList:
                fileWritten = serverDict[ip][1]
                if fileWritten == False:
                    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                    bytesToSend         = str.encode("Resend Message")
                    UDPClientSocket.sendto(bytesToSend, (ip, 9056)) 
                    rr = asyncio.create_task(request_resend())

        if t in done:
            ip,bytes = t.result()
            serverMsg = bytes.decode('utf-8')
            serverIp = ip[0]

            msgTup = ast.literal_eval(serverMsg)
            if isinstance(msgTup, tuple) == False:
                print("Error: Message is not a tuple")
            elif len(msgTup) != 3:
                print("Error: Message is not the correct length")
            elif isinstance(msgTup[0], int) == False or isinstance(msgTup[1], int) == False:
                print("Error: Message does not contain valid values")
            current_part = msgTup[0]
            total_parts = msgTup[1]
            msg = msgTup[2]

            msgDict = serverDict[serverIp][0]
            fileWritten = serverDict[serverIp][1]
            serverDict[serverIp][0][current_part] = msg

            partsDict[serverIp] = total_parts

            if len(msgDict) == total_parts and fileWritten == False: #writeout each ppm file from individual servers
                print("Received All Messages From ", serverIp)
                filename = "out." + ip[0] + ".ppm"
                outputFile = open(filename, "w")
                ppm_string = ""
                for i in range(len(msgDict)):
                    if i in msgDict:
                        outputFile.write(msgDict[i])
                        ppm_string += msgDict[i]
                    else:
                        print("ERROR: Missing Line")
                outputFile.close()
                combinedDict[serverIp] = ppm_string
                serverDict[serverIp] = (serverDict[serverIp][0], True)

            t = asyncio.create_task(chan.get())

asyncio.run(main())
