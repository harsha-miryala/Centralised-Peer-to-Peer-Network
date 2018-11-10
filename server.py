import socket
import _thread
import pickle
import time

serverPort = 12000
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.bind(("", serverPort))
listoffiles = ['ace.txt','2', '125.78.54.89', 'bad.txt','3', '125.78.57.19', 'cat.txt','5','125.78.50.8']
clientaddresslist=[]
listofrequestmessages=[]
partialmessages=[]
clientack=[]

print("The server is ready to receive")
print(socket.gethostbyname(socket.gethostname()))
partial=0

def serverprocess(receiveddata,clientaddress):
    print("Server received one message")
    partial=0
    receivedstring=receiveddata.decode('utf-8')
    print(receivedstring)
    x=0
    temp=''
    requestmessage=[]
    while x<len(receivedstring):
        if (receivedstring[x]!=' ' and receivedstring[x]!='!' and x!=len(receivedstring)-1):
            temp=temp+receivedstring[x]
            x+=1
            continue
        elif x==len(receivedstring)-1:
            x+=1
            requestmessage.append(temp)
            temp=''
        else:
            x+=1
            requestmessage.append(temp)
            temp=''
    
    #listofrequestmessages.append(requestmessage)
    
    print('Request Message/Received String :', receivedstring)
    
    #print('Request Message as a list :', requestmessage)
    
    if(requestmessage[3]=='200'):
        print('Client Ack Received')
        clientack.append(clientaddress)
        clientack.append(requestmessage[0])
        clientack.append(requestmessage[2])
    
    else:
        receivedseqnumber=int(requestmessage[0])
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
                if(clientaddress==partialmessages[y] and requestmessage[1]==partialmessages[y+1]):  #include check for sequence number
                    present=1
                    print('Partial Message was already received...combining this message with the previous message')
                    receivedstring=partialmessages[y+2]+tempstring
                    if(receivedstring[len(receivedstring)-1]=='!'):
                        print('Full message combined..Server will respond appropriately')
                        print(receivedstring)
                    else:
                        print('The message is still partial, waiting for next packet...')
                        partialmessages[y+2]=receivedstring
                        responsemessage = []
                        responsemessage.append(str(receivedseqnumber))
                        responsemessage.append(requestmessage[1])
                        responsemessage.append(str(partial))
                        responsemessage.append('PartialMessageReceived')
                        responsemessage.insert(4,200)
                        responsemessage.insert(5,'Success')
                        print('Response Message:', responsemessage)
                        serverSocket.sendto(pickle.dumps(responsemessage), clientaddress)
                y+=3
            if present==0:
                print('First partial message received..storing it for combining when the next message comes..')
                partialmessages.append(clientaddress)
                partialmessages.append(requestmessage[1])
                partialmessages.append(receivedstring)
                responsemessage = []
                responsemessage.append(str(receivedseqnumber))
                responsemessage.append(requestmessage[1])
                responsemessage.append(str(partial))
                responsemessage.append('PartialMessageReceived')
                responsemessage.insert(4,200)
                responsemessage.insert(5,'Success')
                print('Response Message:', responsemessage)
                serverSocket.sendto(pickle.dumps(responsemessage), clientaddress)
        #print(receivedstring[len(receivedstring)-1])
        if(receivedstring[len(receivedstring)-1]=='!'):
            print('Processing full string: ', receivedstring)
            requestmessage=[]
            x=0
            temp=''
            while x<len(receivedstring):
                if (receivedstring[x]!=' 'and receivedstring[x]!='!'):
                    temp=temp+receivedstring[x]
                    x+=1
                    continue
                else:
                    x+=1
                requestmessage.append(temp)
                temp=''
            #print('Request Message as a list: ', requestmessage)
            if requestmessage[3] == 'QueryForContent':
                responsemessage = []
                responsemessage.append(str(receivedseqnumber))
                responsemessage.append(str(requestmessage[1]))
                responsemessage.append(str(partial))
                responsemessage.append(requestmessage[3])
                print('Query received')
                count = 0
                identifier = 0
                while count < len(listoffiles):
                    if requestmessage[6] == listoffiles[count]:
                        if identifier==0:
                            responsemessage.insert(4,'200')
                            responsemessage.insert(5,'Success')
                        responsemessage.append(listoffiles[count])
                        responsemessage.append(listoffiles[count+1])
                        responsemessage.append(listoffiles[count+2])
                        #print('Response Message:', responsemessage)
                        identifier=1            #change here for all files list

                    elif requestmessage[6]=='':
                        if identifier==0:
                            responsemessage.insert(4,'200')
                            responsemessage.insert(5,'Success')
                        responsemessage.append(listoffiles[count])
                        responsemessage.append(listoffiles[count+1])
                        responsemessage.append(listoffiles[count+2])
                        #print('Response Message:', responsemessage)
                        identifier=1
                    count = count + 3


                if identifier == 0:
                    responsemessage.insert(4,'400')
                    responsemessage.insert(5,'Error')
                    #print('Response Message:', responsemessage)
                print('Response Message:', responsemessage)
                temp=' '.join(responsemessage)
                temp+='!'
                serverSocket.sendto(pickle.dumps(responsemessage[0:5]), clientaddress)
                if(len(temp)>128):
                    partial=1
                    responsemessage[2]=str(partial)
                    temp=' '.join(responsemessage)
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
                    print('Message that is sent:',tobesent)
                    serverSocket.sendto(bytes(tobesent,'utf-8'), clientaddress)
                    time.sleep(2)      #remove this
                    #print(clientack)    #remove this
                    if(len(temp)>128):
                        xcount=0
                        while xcount<len(clientack):
                            #print(clientaddress,str(int(receivedseqnumber)+1))     #remove this
                            if clientack[xcount]==clientaddress and clientack[xcount+1]==str(int(receivedseqnumber)+1) and (clientack[xcount+2]=='PartialMessageReceived' or clientack[xcount+2]=='FullMessageReceived'):
                                print('Acknowledgement received...continuing')
                                receivedseqnumber+=1
                                break
                            else:
                                xcount+=3
                        if clientack[xcount+2]=='FullMessageReceived':
                            print('Client says full message received')
                            #clientack.pop(xcount)
                            #clientack.pop(xcount+1)
                            #clientack.pop(xcount+2)
                            break
                        tobesent=str(receivedseqnumber)+' '+str(requestmessage[1])+' '+str(partial)+' '
                    else:
                        break

                #serverSocket.sendto(pickle.dumps(responsemessage), clientaddress)

            if requestmessage[3] == 'InformAndUpdate':
                responsemessage = []
                responsemessage.append(receivedseqnumber)
                responsemessage.append(requestmessage[1])
                responsemessage.append(str(partial))
                responsemessage.append(requestmessage[3])
                responsemessage.append(200)
                responsemessage.append('Success')
                print('Inform and update message received')
                count=6
                while count<len(requestmessage):
                    listoffiles.append(requestmessage[count])
                    listoffiles.append(requestmessage[count+1])
                    listoffiles.append(clientaddress[0])
                    count+=2
                print('New updated list', listoffiles)
                #responsemessage.insert(0, 'Success')
                print('Response Message:', responsemessage)
                serverSocket.sendto(pickle.dumps(responsemessage), clientaddress)

                #For processing a exit message
            if requestmessage[3]=='Exit':
                count=0
                while count<len(listoffiles):
                    if(listoffiles[count]==clientaddress[0]):
                        listoffiles.pop(count)
                        listoffiles.pop(count-1)
                        listoffiles.pop(count-2)
                        count=count-3
                    count+=1
                responsemessage = []
                responsemessage.append(str(receivedseqnumber))
                responsemessage.append(requestmessage[1])
                responsemessage.append(str(partial))
                responsemessage.append(requestmessage[3])
                responsemessage.append(200)
                responsemessage.append('Success')
                print('New updated list', listoffiles)
                print('Response Message:', responsemessage)
                serverSocket.sendto(pickle.dumps(responsemessage), clientaddress)
    print('Exiting one thread')

while 1:
    ReceivedData=''
    ReceivedData, clientAddress = serverSocket.recvfrom(2048)
    _thread.start_new_thread(serverprocess,(ReceivedData,clientAddress))







