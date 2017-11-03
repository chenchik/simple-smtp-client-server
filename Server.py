'''
Created on March 20th, 2017

@author: danila chenchik
I agree to the UNC honor pledge
'''
import sys
from socket import *
from cStringIO import StringIO
from __builtin__ import False
from _sqlite3 import connect

specialchars = ["<" , ">" , "(" , ")" , "[" , "]" , "\\" , "."
 , "," , ";" , ":" , "@" , "\""]
err = "ERROR -- "
mailstr = "MAIL"
fromstr = "FROM"
rcptstr = "RCPT"
tostr = "TO"
datastr = "DATA"
mailfromstr = "mail-from-cmd"
pathstr = "path"
mailboxstr = "mailbox"
localpartstr = "local-part"
domainstr = "domain"
elemstr = "element"
senderok = "Sender ok"

_cmd_error = "500 Syntax error: command unrecognized"
_param_error = "501 Syntax error in parameters or arguments"
_order_error = "503 Bad sequence of commands"
_data_start_str = "354 Start mail input; end with <CRLF>.<CRLF>"
_ok = "250 OK"
_quit_response = "221 goodbye"
_missing_param_port = "Please specify a port number."

_response_list = [_cmd_error , 
                _param_error , 
                _order_error , 
                _data_start_str , 
                _ok ]

_mail_from_code = 0
_rcpt_to_code = 1
_data_code = 2

_rcpt_log = ""
_user_log = []

_server_welcome_message = "220 welcome to "
_helo = "HELO"
_helo_ack = "250 "
_helo_ack_part_2 = " pleased to meet you"
_unacceptable_helo = "Received a bad HELO from the client"
_retry_port = "Couldn't connect to that port...attempting to connect to port "
_bad_client_command = "The server encountered an invalid SMTP command."
_server_socket_error_handshake = "The server encountered a client socket error during the handshake process"
_server_socket_error_commands = "The server encountered a client socket error during the command exchange"

_quit = "QUIT"

_prev_cmd_key = "prev_cmd"
_in_data_mode_key = "in_data_mode"
_line_delim = "\n"

def append_to_log(line, cmd_code, cmd):
    global _rcpt_log, _user_log
    #append messages to user forward directory
    if(cmd_code == _mail_from_code):
        _rcpt_log = _rcpt_log + "From: " + cmd
    elif(cmd_code == _rcpt_to_code):
        _rcpt_log = _rcpt_log + "To: " + cmd
    else:
        _rcpt_log += line
    #append to users log if we are current doing iun the RCPT TO command
    if(cmd_code == _rcpt_to_code):
        cmd = cmd.strip()
        cmd = cmd.strip("<")
        cmd = cmd.strip(">")
        _user_log.append(cmd)
    return True

def clear_log():
    global _rcpt_log, _user_log
    _rcpt_log = ""
    #clear the user log list
    _user_log[:] = []
    return True

def get_user_domain(user):
#
    return user.split("@")[1]

def append_to_files():
    for user in _user_log:
        user_domain = get_user_domain(user)
        user_file = open("./forward/"+user_domain, "a")
        user_file.write(_rcpt_log)

    clear_log()
    return True

def too_long(path, pos, strng):
    #array/string out of bounds checker
    if(len(path)-1 < pos):
        print strng
        return True
    
    return False

def validate_char(char):
    #check if ascii, if not return false
    #check if is a special character, if it is, return false
    #check if space, if it is return false
    #otherwise return true
    if(ord(char) >= 128):
        return False

    for i in specialchars:
        if(char == i):
            return False

    if(char.isspace()):
        return False

    return True

def validate_string(string, pos):
    #check to to see if first character is char 
    if(not validate_char(string[pos])):
        return -1
    
    charCheck = True
    while(charCheck):
        pos = pos+1
        #perform a non typical length check
        if(pos >= len(string)):
            charCheck = False
        else:
            charCheck = validate_char(string[pos])

    #at this point, we should return the position of the non char character
    return pos

def validate_local_part(path, pos):
    #check length
    if(too_long(path, pos, _param_error)):return -1
    
    #validate the string
    pos = validate_string(path, pos)
    if(pos == -1):
        print _param_error
        return -1
    
    #check length
    if(too_long(path, pos, _param_error)):return -1

    return pos

def validate_first_elem_chars(path, pos):
    #check first symbol
    if(not path[pos].isalpha()):
        print _param_error
        return -1
    
    #check length
    pos = pos + 1
    if(too_long(path, pos, _param_error)):return -1
    
    #check second character is let-dig-str  
    if(not path[pos].isalnum()):
        print _param_error
        return -1
    
    pos = pos + 1
    return pos
    

def validate_elements(path, pos):
    beginElem = True
    looping = True
    while(looping):
        #check length
        if(too_long(path, pos, _param_error)):return -1
        
        if(beginElem):
            #check initial element symbols
            pos = validate_first_elem_chars(path, pos)
            if(pos == -1):
                return -1
            beginElem = False
        else:
            #check the rest of the elements
            #check for separation of elements
            if(path[pos] == "."):
                pos = pos + 1
                beginElem = True
                
            #check for other chars in elements
            else:
                if(not path[pos].isalnum()):
                    looping = False
                else:
                    pos = pos + 1
    return pos

def validate_domain(path, pos):
    #check length
    if(too_long(path, pos, _param_error)):return -1
    
    pos = validate_elements(path, pos)
    if(pos == -1):
        return -1
    
    return pos

def validate_mailbox(path, pos):
    pos = validate_local_part(path, pos)
    if(pos == -1):
        return -1

    #check length
    if(too_long(path, pos, _param_error)):return -1

    #check for separation character
    if(path[pos] != "@"):
        print _param_error
        return -1
    
    pos = validate_domain(path, pos+1)
    if(pos == -1):
        return -1
    
    return pos

def validate_path(path):
    n = len(path)
    #make sure it at least has "<>"
    if(n < 2):
        print _param_error
        return -1

    #check initial path character
    if(path[0] != "<"):
        print _param_error
        return -1
    
    #start parsing mailbox at position 1 
    pos = validate_mailbox(path, 1)
    if(pos == -1):
        return -1

    #validate last path symbol
    if(path[pos] != ">"):
        print _param_error
        return -1
    
    #length check
    pos = pos + 1
    if(too_long(path, pos, _param_error)):return -1
        
    return pos

def validate_mail_from_and_rcpt_to_str(tup):
    #check first charcter
    if(len(tup[0]) > 1):
        if(tup[0][0].isspace()):
            return -1

    #split on all whitespace in betweewn 'from' and 'to' on first space
    cmd_str = tup[0].split(None,1)
    if(len(cmd_str) != 2):
        return -1
   
    #check that MAIL and FROM are exactly that
    if((cmd_str[0] == mailstr) & (cmd_str[1] == fromstr)):
        #return command code for mail from 
        return _mail_from_code
    
    #check that RCPT and TO are exactly that
    elif((cmd_str[0] == rcptstr) & (cmd_str[1] == tostr)):
        #return code for rcpt to
        return _rcpt_to_code

    return -1

def validate_data_str(tup):
    #strip all white spoace to the right
    cmd_str = tup[0].rstrip()
    if(cmd_str != datastr):
        return -1
    
    return _data_code

def validate_order(cur_cmd, prev_cmd):
    #if the previous coimmand was DATA the current command has to be MAIL FROM
    if((prev_cmd == _data_code) & (cur_cmd != _mail_from_code)):
        print _order_error
        return -1
    
    #if the previous command was MAIL FROM, the current command must be RCPT TO
    elif((prev_cmd == _mail_from_code) & (cur_cmd != _rcpt_to_code)):
        print _order_error
        return -1
        
    #if the last command was RCPT TO, the current command simply cant be MAIL FROM
    elif((prev_cmd == _rcpt_to_code) & (cur_cmd == _mail_from_code)):
        print _order_error
        return -1
       
    return cur_cmd

def get_pos_after_data_str(cmd):
    if(len(cmd) < 5):
        print _cmd_error
        return -1

    if(cmd[:4] != "DATA"):
        print _cmd_error
        return -1
    return 4

def check_ending(line, cmd, pos, cmd_code, error_str, success_str): 
    #do the backslash n and whitespace check
    n = len(cmd)
    if(cmd[n-1] != "\n"):
        print _param_error
        return -1
    
    #loop through everything except the \n at the end, which we already checked
    while(pos < n-1):
        if(not cmd[pos].isspace()):
            print _param_error
            return -1
        pos = pos + 1

    print success_str
    #only append to log if its not the data command
    if(cmd_code != _data_code):
        append_to_log(line, cmd_code, cmd)
    return pos


def validate_command(line, prev_cmd):
    #split and limit to one split
    tup = line.split(":",1)
     
    #check mail from and rcpt to strings
    cur_cmd = validate_mail_from_and_rcpt_to_str(tup)   
    if(cur_cmd == -1):
        #check data string
        cur_cmd = validate_data_str(tup)
        if(cur_cmd == -1):
            print _cmd_error
            clear_log()
            return -1
        
    #check ordering
    if(validate_order(cur_cmd, prev_cmd) == -1):
        clear_log()
        return -1
      

    #get everything to the right of the first colon, we set max of split to 1 split previously
    rightOfColon = "" 
    #initial position is 0
    pos = 0

    if(cur_cmd != _data_code):
        rightOfColon = tup[1]
        #check left for nullspace
        strippedRightOfColon = rightOfColon.lstrip()
        pos = validate_path(strippedRightOfColon)
        #if there was an error clear the log and dont proceed
        if(pos == -1):
            clear_log()
            return -1
        pos = check_ending(line, strippedRightOfColon, pos, cur_cmd, _param_error, _ok)
        if(pos == -1):
            clear_log()
            return -1
    else:
        #validate the ending of the data command
        rightOfColon = tup[0]
        pos = get_pos_after_data_str(rightOfColon)
        if(pos == -1):
            clear_log()
            return -1
        pos = check_ending(line, rightOfColon, pos, cur_cmd, _cmd_error, _data_start_str)
        if(pos == -1):
            clear_log()
            return -1
 
    return cur_cmd

def validate_data(line, socket):
    if(line != "."):
        append_to_log(line + _line_delim, _data_code, line)
        #return that we are still in data_mode
        return True
        
    #respond to client with _ok
    socket.send(_ok.encode())
    
    append_to_files()
    return False

#method for validating the HELO sent by the client            
def check_helo(helo_message):
    #check if helo message is "HELO" in beginning
    split_helo = helo_message.split(None,1) 
    if(split_helo[0] != _helo):
        return False
    
    #check length and that it actually has a domain/hostname field
    if(len(split_helo) < 2):
        return False
    
    #validate the domain/hostname field
    if(validate_domain(split_helo[1], 0) == -1):
        return False
    
    #if we get to this point, everything is okay
    return True
    
#method for handling the QUIT statement
def handle_quit(line, socket):
    #check ending
    if(line[len(line)-1] != "\n"):
        return -1

    line_list = line.split()
    #make sure its only the quit command 
    if(len(line_list) != 1):
        return -1

    #make sure QUIT was typed
    if(line_list[0] != _quit):
        return -1

    #if we get here, everything is fine, we dont need to send anything back
    return 1

#method for specifically handling the data section of the smtp message
def handle_data_section(line, in_data_mode, socket):

    #split by \n
    line = line.splitlines()
    #keep looping until we know we processed a "."
    while(in_data_mode):
        #we dont know how many lines we've recieved from the client, so we have split on how many we've recieved
        for single_line in line:
            #validate the current line
            in_data_mode = validate_data(single_line, socket)

            #if we are not in_data_mode, that means we just processed a "."
            if(not in_data_mode):
                return True

        #get the new stuff that the client sent if we didn't recieve a "." in the last packet group
        line = socket.recv(4096).decode()
        line = line.splitlines()
    
    return False

def handle_all_cmds(socket):

    #start assuming we just finished a full command
    prev_cmd = _data_code
    in_data_mode = False
    expecting_quit = False
    
    
    #keep processing until we think we should recieve a QUIT cmd
    while(not expecting_quit):
        #get the line sent by the client
        line = socket.recv(4096).decode()
        
        if(not in_data_mode):

            #change stdout to a string
            old_stdout = sys.stdout
            sys.stdout = new_sys_out = StringIO()
            
            prev_cmd = validate_command(line, prev_cmd)
            #if we had an error, restart and go back to waiting state for MAIL FROM, as if we just finished a full sequence of commands
            if(prev_cmd == -1):
                prev_cmd = _data_code
                
                #quit analyzing the commands and    
                #respond to client with the output that was saved in stringIO
                socket.send(new_sys_out.getvalue().encode())
                #change back to normal sys.stdout
                sys.stdout = sys.__stdout__
                return -1

            #if we just had a DATA command, start being inm DATA mode
            elif(prev_cmd == _data_code):
                in_data_mode = True

            #respond to client with the output that was saved in stringIO
            socket.send(new_sys_out.getvalue().encode())
            #change back to normal sys.stdout
            sys.stdout = sys.__stdout__
        
        #if we just encountered a "DATA" command, simply use all text as the input
        else:
            #if we encounter the ".", that means we are expecting a QUIT
            expecting_quit = handle_data_section(line,in_data_mode, socket)
    
    #check to make sure that the quit command was valid
    line = socket.recv(4096).decode()
    return handle_quit(line, socket)

def init_socket():
    if(len(sys.argv) > 1):
        port = int(sys.argv[1])
        server_socket = socket(AF_INET, SOCK_STREAM)
        
        #handle connecting to the port
        retry = True
        while(retry):
            retry = False
            try:
                server_socket.bind(('', port))
            except:
                #do a while loop and keep retrying with incrementing the port num until we find an available one
                port += 1
                print _retry_port + str(port)
                retry = True
        
                
        #open up socket with one thread
        server_socket.listen(1)
        while(True):  
            #initial setup
            connectionSocket, addr = server_socket.accept()
            
            #setup try to account for socket errors    
            try:     
                server_hostname = getfqdn()
                welcome = _server_welcome_message + server_hostname
                connectionSocket.send(welcome.encode())
    
                #get the HELO message from the client
                helo = connectionSocket.recv(1024).decode()
                #validate the HELO message
                if(not check_helo(helo)):
                    connectionSocket.send(_cmd_error.encode())
                    print _unacceptable_helo
                    connectionSocket.close()
                    continue

                #send the HELO ack
                helo_ack_str = _helo_ack + helo + _helo_ack_part_2
                connectionSocket.send(helo_ack_str.encode())

            except:
                print _server_socket_error_handshake
                connectionSocket.close()
                clear_log()
                continue

            try:

                #respond to the client commands
                response = handle_all_cmds(connectionSocket)
                if(response == -1):
                   print _bad_client_command
    
            except:
                print _server_socket_error_commands
           
            #close the connectionSocket
            connectionSocket.close()
            #clear the log just in case
            clear_log()
                   
    else:
        print _missing_param_port
    
    return 1
      
def main():
    init_socket()
    return 1
    
main()
