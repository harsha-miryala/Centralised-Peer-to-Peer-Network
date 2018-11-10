import socket
import pickle
import _thread
import time
from timeit import default_timer
import sys

def p2pserver():
    serverPort = 11000
    serverSockettcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSockettcp.bind(('', serverPort))
    serverSockettcp.listen(1)
    print('Note: This p2p client is now acting as a transient server to serve other p2p client\nYou will see intermediate processing messages when it serves other p2p clients.')
    print('\nThe P2P server is ready to send files.')
    i=0

    def serverprocess(connectionsocket ,address):
        print('Connected in this connection: ',connectionsocket)
        fullpath='/home/harsha/Downloads/Centralised-Peer-to-Peer-Network/Send/'
        Response=[]
        gotthis = connectionsocket.recv(1024)
        gotthis=pickle.loads(gotthis)
        requeststring=' '.join(gotthis)
        print(requeststring)
        #sentencestring= sentence.decode("utf-8")
        fullpath += gotthis[1]
        error=''
        try:
            f = open(fullpath, 'r')
            strf=f.read()
            print(len(strf))
        except Exception as errtxt1:
            error=str(errtxt1)
            print(errtxt1)
            print('File Not Found')
        sendthis=[]
        if(gotthis[2]!='HTTP/1.1'):
             sendthis.append('HTTP/1.1')
             sendthis.append('505')
             sendthis.append('HTTPVersionNotSupported')
             sendthis=' '.join(sendthis)
             print(sendthis)
             connectionsocket.sendall(bytes(sendthis,'utf-8'))

        elif(gotthis[0]!='GET'):
            sendthis.append('HTTP/1.1')
            sendthis.append('400')
            sendthis.append('BadRequest')
            sendthis=' '.join(sendthis)
            print(sendthis)
            connectionsocket.sendall(bytes(sendthis,'utf-8'))

        elif(len(error)==0):
             sendthis.append('HTTP/1.1')
             sendthis.append('200')
             sendthis.append('Ok')
             sendthis.append(str(len(strf)))
             sendthis=' '.join(sendthis)
             sendthis+=' '+strf
             print('File was sent')
             #print(sendthis)
             connectionsocket.sendall(bytes(sendthis,'utf-8'))

        else:
            sendthis.append('HTTP/1.1')
            sendthis.append('404')
            sendthis.append('NotFound')
            sendthis=' '.join(sendthis)
            print(sendthis)
            connectionsocket.sendall(bytes(sendthis,'utf-8'))

        #gotthis = connectionsocket.recv(1024)
        #gotthis=pickle.loads(gotthis)
        #print(gotthis)
        #if(gotthis[1]=='200' and gotthis[3]=='ReadyToReceive'):
         #   connectionsocket.sendall(bytes(strf,'utf-8'))
            #print('Enter an input to show multithreading: ')
            #x=input();
        #elif(gotthis[1]=='400' and gotthis[3]=='CloseConnection'):
         #   print('Client acknowledges the error')   

        print('Closing Connection')
        connectionsocket.close()


    while 1:
        connectionSocket, addr = serverSockettcp.accept()
        _thread.start_new_thread(serverprocess,(connectionSocket,addr))


def p2pinterface():
    #print('Thread started')
    # change to server IP address when running on a different machine
    serverName = socket.gethostbyname(socket.gethostname()) 
    serverPort = 12000
    thisaddr=socket.gethostbyname(socket.gethostname())
    thishost=socket.gethostname()
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    seqnumber,reqnumber,partial=0,0,0
    partialmessages=[]
    alpha=0.125
    beta=0.25
    EstimatedRtt=2        #Default starting values
    TimeoutInterval=2     #Default starting values
    DevRtt=0
    #To request for a file
    time.sleep(0.1)

    while 1:
        print('\nClient Interface:\n1. Query for Content\n2. Inform and Update\n3. Exit\n4. Ask for a file from a peer')
        reqnumber+=1
        seqnumber+=1
        partial=0
        print('\nEnter your choice: ')
        choice= int(input())
        if choice==1:
            RequestMessage=[]
            RequestMessage.append(str(seqnumber))
            RequestMessage.append(str(reqnumber))
            RequestMessage.append(str(partial))
            RequestMessage.append('QueryForContent')
            RequestMessage.append(thishost)
            RequestMessage.append(thisaddr)
            filename = input('Input file name(or press enter to get full directory listing): ')
            RequestMessage.append(filename)
            #RequestMessage = ['Query for content', message]
            temp=' '.join(RequestMessage)
            temp+='!'
            if(len(temp)>128):
                partial=1
                RequestMessage[2]=str(partial)
                temp=' '.join(RequestMessage)
                temp+='!'
            print(temp)
            x=0
            tobesent=''
            while(x<len(temp)):
                while(x<len(temp)):
                    if(len(tobesent+temp[x])<=128):
                        tobesent+=temp[x]
                        x+=1
                    else:
                        break
                while 1:
                    print('Message that is sent:',tobesent)
                    start = default_timer()
                    clientSocket.sendto(bytes(tobesent,'utf-8'), (serverName, serverPort))
                    try:
                        clientSocket.settimeout(TimeoutInterval)
                        ReceivedData, serverAddress = clientSocket.recvfrom(2048)
                        SampleRtt = default_timer() - start
                        clientSocket.settimeout(None)     #waiting maybe near this line...??
                        EstimatedRtt=((1-alpha)*EstimatedRtt)+(alpha*SampleRtt)
                        DevRtt=((1-beta)*DevRtt)+(beta*abs(SampleRtt-EstimatedRtt))
                        TimeoutInterval=EstimatedRtt+(4*DevRtt)
                        ResponseMessage=pickle.loads(ReceivedData)
                        #print(ResponseMessage)
                        if(ResponseMessage[0]==str(seqnumber) and partial==1 and (ResponseMessage[3]=='PartialMessageReceived') and ResponseMessage[5]=='Success'):
                            print('Got Partial Message Acknowledgement')
                            break #Break from the while 1 loop..kind of do while loop
                        elif (ResponseMessage[0]==str(seqnumber) and ResponseMessage[3]=='QueryForContent'):
                            break
                        else:
                            continue
                    except Exception as errortext:
                        print('Timed Out')
                        continue
                if(ResponseMessage[3]=='QueryForContent'):
                    print('Got Full Acknowledgement')
                    break
                seqnumber+=1
                tobesent=str(seqnumber)+' '+str(reqnumber)+' '+str(partial)+' '
                #clientSocket.sendto(bytes(tobesent,'utf-8'), (serverName, serverPort))

            while 1:                                                            #for receiving entire response
                receivedstring, serverAddress = clientSocket.recvfrom(2048)
                #ResponseMessage=pickle.loads(ReceivedData)
                receivedstring=receivedstring.decode('utf-8')
                print('Received String', receivedstring)
                x=0
                temp=''
                requestmessage=[]
                while x<len(receivedstring):
                    if (receivedstring[x]!=' ' and receivedstring[x]!='!'):
                        temp=temp+receivedstring[x]
                        x+=1
                        continue
                    else:
                        x+=1
                    requestmessage.append(temp)
                    temp=''
                #listofrequestmessages.append(requestmessage)
                #print('Request Message/Received String :', receivedstring)
                receivedseqnumber=requestmessage[0]
                if(requestmessage[2]=='1'):
                    print('Received message is a partial message..processing it now..')
                    #Extracting data part alone removing seq no.,req no.,partial bits and store temporarily
                    count,spaces=0,0
                    while count<len(receivedstring):
                        if(receivedstring[count]==' ' and spaces<3):
                            spaces+=1
                        elif spaces==3:
                            break
                        count+=1
                    tempstring=''
                    while(count<len(receivedstring)):
                        tempstring+=receivedstring[count]
                        count+=1
                    #checking for another part of partial message already present
                    y,present=0,0
                    while(y+2<len(partialmessages)):
                        if(serverAddress==partialmessages[y] and requestmessage[1]==partialmessages[y+1]):  #include check for sequence number
                            present=1
                            print('Partial Message was already received...combining this message with the previous message')
                            receivedstring=partialmessages[y+2]+tempstring
                            if(receivedstring[len(receivedstring)-1]=='!'):
                                print('Full message combined')
                                print(receivedstring)
                                responsemessage = []
                                responsemessage.append(str(int(receivedseqnumber)+1))
                                seqnumber+=1#seq numner+=1
                                responsemessage.append(requestmessage[1])
                                responsemessage.append('FullMessageReceived')
                                responsemessage.insert(4,'200')
                                responsemessage.insert(5,'Success')
                                print('Response Message:', responsemessage)
                                ackmessage=' '.join(responsemessage)
                                clientSocket.sendto(bytes(ackmessage,'utf-8'), (serverName, serverPort))

                            else:
                                print('The message is still partial, waiting for next packet...')
                                partialmessages[y+2]=receivedstring
                                responsemessage = []
                                responsemessage.append(str(int(receivedseqnumber)+1))#seqnumber+=1
                                seqnumber+=1
                                responsemessage.append(requestmessage[1])
                                responsemessage.append('PartialMessageReceived')
                                responsemessage.insert(4,'200')
                                responsemessage.insert(5,'Success')
                                print('Response Message:', responsemessage)
                                ackmessage=' '.join(responsemessage)
                                clientSocket.sendto(bytes(ackmessage,'utf-8'), (serverName, serverPort))
                            y+=3
                        else:
                            y+=3
                    if present==0:
                        print('First partial message received..storing it for combining when the next message comes..')
                        partialmessages.append(serverAddress)
                        partialmessages.append(requestmessage[1])
                        partialmessages.append(receivedstring)
                        responsemessage = []
                        responsemessage.append(str(int(receivedseqnumber)+1))#seqnumber+=1
                        seqnumber+=1
                        responsemessage.append(requestmessage[1])
                        responsemessage.append('PartialMessageReceived')
                        responsemessage.insert(4,'200')
                        responsemessage.insert(5,'Success')
                        print('Response Message:', responsemessage)
                        ackmessage=' '.join(responsemessage)
                        clientSocket.sendto(bytes(ackmessage,'utf-8'), (serverName, serverPort))
                #print(receivedstring[len(receivedstring)-1])
                if(receivedstring[len(receivedstring)-1]=='!'):
                    print('Processing full string: ', receivedstring)
                    receivedmessage=[]
                    x=0
                    temp=''
                    while x<len(receivedstring):
                        if (receivedstring[x]!=' 'and receivedstring[x]!='!'):
                            temp=temp+receivedstring[x]
                            x+=1
                            continue
                        else:
                            x+=1
                        receivedmessage.append(temp)
                        temp=''
                    #print('Response Message as a list: ', receivedmessage)

                    if receivedmessage[5] == 'Success':
                        print('\nThe file list, file size and corresponding peers: ')
                        count=6
                        while count<len(receivedmessage):
                            print(receivedmessage[count],' ',receivedmessage[count+1],' ',receivedmessage[count+2])
                            count+=3
                    elif receivedmessage[5]=='Error':
                        print('The file is not available in any of the peers')
                    break
        
        #Inform and Update
        if choice==2:
            RequestMessage=[]
            RequestMessage.append(str(seqnumber))
            RequestMessage.append(str(reqnumber))
            RequestMessage.append(str(partial))
            RequestMessage.append('InformAndUpdate')
            RequestMessage.append(thishost)
            RequestMessage.append(thisaddr)
            while 1:
                filename = input('Input file name that you have: ')
                RequestMessage.append(filename)
                filesize= input('Size of the file: ')
                RequestMessage.append(filesize)
                check=input('Do you want to inform about other files you have?(yes/no)')
                if check=='no':
                    break
           # RequestMessage = ['Inform and update', message]
            #clientSocket.sendto(pickle.dumps(RequestMessage), (serverName, serverPort))
            temp=' '.join(RequestMessage)
            temp+='!'
            if(len(temp)>128):
                partial=1
                RequestMessage[2]=str(partial)
                temp=' '.join(RequestMessage)
                temp+='!'
            print(temp)
            x=0
            tobesent=''
            while(x<len(temp)):
                while(x<len(temp)):
                    if(len(tobesent+temp[x])<=128):
                        tobesent+=temp[x]
                        x+=1
                    else:
                        break
                while 1:
                    print('Message that is sent:',tobesent)
                    start = default_timer()
                    clientSocket.sendto(bytes(tobesent,'utf-8'), (serverName, serverPort))
                    try:
                        clientSocket.settimeout(TimeoutInterval)
                        ReceivedData, serverAddress = clientSocket.recvfrom(2048)   #waiting maybe near this line...??
                        SampleRtt = default_timer() - start
                        clientSocket.settimeout(None)
                        EstimatedRtt=((1-alpha)*EstimatedRtt)+(alpha*SampleRtt)
                        DevRtt=((1-beta)*DevRtt)+(beta*abs(SampleRtt-EstimatedRtt))
                        TimeoutInterval=EstimatedRtt+(4*DevRtt)
                        ResponseMessage=pickle.loads(ReceivedData)
                        print(ResponseMessage)
                        if(ResponseMessage[0]==str(seqnumber) and partial==1 and (ResponseMessage[3]=='PartialMessageReceived') and ResponseMessage[5]=='Success'):
                            print('Got Partial Message Acknowledgement')
                            break #Break from the while 1 loop..kind of do while loop
                        elif (ResponseMessage[0]==seqnumber and ResponseMessage[3]=='InformAndUpdate'):
                            break
                        else:
                            continue
                    except Exception as errortext:
                        print('Timed Out')
                        continue

                if(ResponseMessage[3]=='InformAndUpdate'):
                    break
                seqnumber+=1
                tobesent=str(seqnumber)+' '+str(reqnumber)+' '+str(partial)+' '
            #print('Response Message from Server: ', ResponseMessage)
            if ResponseMessage[5] == 'Success':
                print('Acknowledged by server- The central directory server list was updated accordingly!')
        
        #Exit command
        if choice==3:
            RequestMessage=[]
            RequestMessage.append(str(seqnumber))
            RequestMessage.append(str(reqnumber))
            RequestMessage.append(str(partial))
            RequestMessage.append('Exit')
            RequestMessage.append(thishost)
            RequestMessage.append(thisaddr)
            temp=' '.join(RequestMessage)
            temp+='!'
            while 1:
                print('Message that is sent:',temp)
                start = default_timer()
                clientSocket.sendto(bytes(temp,'utf-8'), (serverName, serverPort))
                try:
                    clientSocket.settimeout(TimeoutInterval)
                    ReceivedData, serverAddress = clientSocket.recvfrom(2048)       #waiting maybe near this line...??
                    SampleRtt = default_timer() - start
                    clientSocket.settimeout(None)
                    EstimatedRtt=((1-alpha)*EstimatedRtt)+(alpha*SampleRtt)
                    DevRtt=((1-beta)*DevRtt)+(beta*abs(SampleRtt-EstimatedRtt))
                    TimeoutInterval=EstimatedRtt+(4*DevRtt)
                    ResponseMessage=pickle.loads(ReceivedData)
                    if (ResponseMessage[0]!=str(seqnumber)):
                        continue
                    print(ResponseMessage)
                except Exception as errortext:
                        print('Timed Out')
                        continue
                if(ResponseMessage[5]=='Success'):
                    print('Server acknowledges exit..all instance of your files in the directory list was removed')
                    break
        
        #Asking for a file from peer
        if choice==4:
            print('Enter the IP of the server you want to get the file from?')
            serverName=input()
            #serverName = socket.gethostbyname(socket.gethostname())
            serverPort = 11000
            clientSockettcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSockettcp.connect((serverName, serverPort))
            print('Ask for a file')
            sentence = input('Input filename: ')
            fullpath ='/home/harsha/Downloads/Centralised-Peer-to-Peer-Network/Receive/'
            fullpath = fullpath+sentence
            sendthis=[]
            sendthis.append('GET')
            sendthis.append(sentence)
            sendthis.append('HTTP/1.1')
            clientSockettcp.send(pickle.dumps(sendthis))
            size=10
            i=0
            spaces=0
            ReceivedData=''
            temp=''
            gotthis=[]
            while size > len(ReceivedData):
                data = clientSockettcp.recv(1024)
                if not data:
                    break
                data=data.decode('utf-8')
                count=0
                while(i==0 and count<len(data)):
                    if(data[count]!=' '):
                        temp=temp+data[count]
                        count=count+1
                    else:
                        gotthis.append(temp)
                        temp=''
                        spaces+=1
                        count+=1
                        if(spaces==4):
                            break
                if(gotthis[1]=='200'):
                    size=int(gotthis[3])
                i=1
                ReceivedData+= data[count:len(data)]
            #print('Status from server: ', Response[0])
            if(gotthis[1]=='200'):
                f = open(fullpath, 'w')
                f.write(ReceivedData)
                print('File was transfered')
                f.close()
            elif(gotthis[1]=='404'):
                print('Server could not find the file..request a different file')
            elif(gotthis[1]=='400'):
                print('Bad Request was sent')
            elif(gotthis[1]=='505'):
                print('HTTP version not supported by server')

            #print('Enter an input to show multithreading: ')
            #x=input();
            clientSockettcp.close()

    # print(modifiedMessage)
    clientSocket.close()

#print('Trying to start thread: ')
try:
    _thread.start_new_thread(p2pinterface,())
    _thread.start_new_thread(p2pserver,())
except Exception as errtxt:
    print(errtxt)
while 1:
    m=3
#y=_thread.start_new_thread(p2pserver,(1,1))










