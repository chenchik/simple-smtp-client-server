'''
Created by Danila Chenchik 02/12/2017
I agree to the UNC honor pledge
'''

import sys
from socket import *

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

_mail_from_code = 0
_rcpt_to_code = 1
_data_code = 2

_rcpt_log = ""
_user_log = []

_mail_from = "MAIL FROM:"
_rcpt_to = "RCPT TO:"
_data = "DATA"
_data_end = "."
_quit = "QUIT"

_forward_mail_from = "From:"
_forward_rcpt_to = "To:"
_forward_subject = "Subject:"

_cmd_error = "500 Syntax error: command unrecognized"
_param_error = "501 Syntax error in parameters or arguments"
_order_error = "503 Bad sequence of commands"
_data_start_str = "354"
_ok = "250"
_quit_response = "221"
_helo_response = "220"

_cmd_line_key = "cmd_line"
_processing_data_key = "processing_data"
_cmd_start = "cmd_start"

_client_HELO = "HELO " 
_end = "."

_from_key = "From: "
_to_key = "To: "
_subject_key = "Subject: "
_message_key = "Message (end message by typing <CRLF>.<CRLF>): "
_line_delim = "\n"

_server_port_connection_error = "We couldn't connect to that server hostname and port combination...closing connection."
_data_error_message = "There was an error encountered while processing the 'DATA' command."
_length_error_message = "Your last command's length was too short."
_generic_error_message = "There was an error while processing your last "
_generic_error_message_2 = "command."
_quit_error_message = "Something when wrong when processing your QUIT command"
_unsuccessful_command_response_1 = "Command: "
_unsuccessful_command_response_2 = " Generated an unsuccessful response: "  
_unacceptable_helo = "hello message sent by server not acceptable"
_unacceptable_helo_ack = "HELO ack wasn't what we were expecting"
_closing_connection = "...closing connection"
_no_quit = "You never sent a QUIT command."
_missing_arg = "You forgot to provide a hostname or port number."
_invalid_from = "Invalid 'from' email, please try again."
_invalid_to_1 = "invalid 'to' email on recipient: "
_invalid_to_2 = ". Please try entering all recipients again."
_socket_error = "An unexpected socket error occurred."
_invalid_server_hostname = "You entered an invalid server hostname, please restart the client with a valid hostname."

'''
#######
SECTION TO HANDLE DOMAIN VALIDATION
#######
'''

def too_long(path, pos, strng):
    #array/string out of bounds checker
    if(len(path)-1 < pos):
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
    #check to to see if all charcters are ascii  
    if(not validate_char(string[pos])):
        return -1
    
    charCheck = True
    while(charCheck):
        pos = pos+1
        #perform a non typical length check
        if(pos >= len(string)):
            charCheck = False
        else:
            charCheck = validate_char(string[pos]);

    #at this point, we should return the position of the non char character
    return pos

def validate_local_part(path, pos):
    #check length
    if(too_long(path, pos, _param_error)):return -1
    
    #validate the string
    pos = validate_string(path, pos)
    if(pos == -1):
        return -1
    
    #check length
    if(too_long(path, pos, _param_error)):return -1

    return pos

def validate_first_elem_chars(path, pos):
    #check first symbol
    if(not path[pos].isalpha()):
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
                #check to make sure that we arent about to go past the length of the path
                if(not path[pos].isalnum() or pos >= (len(path)-1)):
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
        return -1
    
    pos = validate_domain(path, pos+1)
    if(pos == -1):
        return -1
    
    return pos

'''
######
END DOMAIN VALIDATION SECTION
######
'''

#method to get the MAIL FROM or RCPT TO string
def get_response_code(response):
    
    #split the response string by whitespace charcters and return the first elelemtn in the result list
    return response.split()[0]

#method to process the stdin response code
def process_response(response, cmd):
    
    if(len(response) < 1):
        print(_length_error_message)
        return -1

    response_code = get_response_code(response)
    if(cmd == _data):
        if(response_code == _data_start_str):
            return 1
        #otherwise, theres an error
        print(_data_error_message)
        return -1
   
    #if we just sent the QUIT command, we are looking for a 221 response code
    if(cmd == _quit):
        if(response_code == _quit_response):
            return 1
        #if its not a 221 response code, we should return -1
        print(_quit_error_message)
        return -1

    #otherwise we should be receiving a 250 back
    if(response_code == _ok):
        return 1

    #if we make it here, there's an error
    print(_generic_error_message + cmd + _generic_error_message_2)
    return -1

#output the appropriate response given the forward file line
def generate_command(line):
   
    return_str = ""
    #cmd start just represents the command we just processed, ie: MAIL FROM, RCPT TO.
    cmd_start = ""
    #boolean for determining if this is the body of the email
    data_line = True

    #check to see if first character sequence is "From:"
    if(len(line) >= 5):
        if(line[:5] == _forward_mail_from):
            cmd_start += _mail_from 
            return_str += _mail_from
            return_str += line[5:]
            data_line = False
    
    #check to see if first char sequence is To:
    if(len(line) >= 3):
        if(line[:3] == _forward_rcpt_to):
            cmd_start += _rcpt_to
            return_str += _rcpt_to
            return_str += line[3:]
            data_line = False

    #we are processing a line of the email body
    if(data_line):
        return_str += line
 
    return {_cmd_line_key :return_str, _processing_data_key :data_line, _cmd_start :cmd_start } 

#main outer method for generating response codes given the entire forward file
def generate_smtp_commands(data, email_lines):
    
    smtp_commands = ""
    #boolean to check if we are current processing message body
    in_message_body = False
    #initialize last command as empty
    last_cmd = ""
    
    full_smtp_cmds = []

    #get smtp command for "from"
    cmd_vals = generate_command(_from_key + email_lines[_from_key][0])
    #need to save the type of command later
    full_smtp_cmds.append([_from_key, cmd_vals[_cmd_line_key]])
    #get smtp commands for "to"
    for to in email_lines[_to_key]:
        cmd_vals = generate_command(_to_key + to)
        full_smtp_cmds.append([_to_key, cmd_vals[_cmd_line_key]])

    #append DATA command
    full_smtp_cmds.append([_data, _data + _line_delim])

    #append the data, which was the full email string
    #split by \n
    message = data.splitlines()
    for line in message:
        #be sure to add \n to account for its loss in the "split()" method
        full_smtp_cmds.append([_message_key, line + _line_delim])

    #append QUIT to the end of the string 
    full_smtp_cmds.append([_quit, _quit + _line_delim]) 
            
    #if we made it here, everything is okay and we can quit
    return full_smtp_cmds

#method for checking the ack sent back from the server to the HELO message we sent
def helo_ack_check(helo_ack):
    if(helo_ack.split(None, 1)[0] != _ok):
        return False
    return True

#method for setting up the from email given what the user typed in
def get_from_email():
    last_line = raw_input(_from_key)
    #validate the email address starting at position 0
    loop_val = -1
    while(loop_val == -1):
        loop_val = validate_mailbox(last_line, 0)
        if(loop_val == -1):
            print _invalid_from
            last_line= raw_input(_from_key)

    return "<" + last_line + ">" + _line_delim

#method for setting up the to email given what the user typed in
def get_to_emails():
    last_line = raw_input(_to_key)
    #separate emails by comma to get all to recipients 
    to_emails = last_line.split(',')
    loop_val = -1
    all_to_emails = []
    while(loop_val == -1):
        #use iterator for printing which email was incorrect
        iterator = 1
        for email in to_emails:
            email = email.lstrip()
            #validate email
            loop_val = validate_mailbox(email, 0)
            if(loop_val == -1):
                print _invalid_to_1 + str(iterator) + _invalid_to_2
                #empty the email list
                all_to_emails[:] = []
                #get the new recipients
                last_line = raw_input(_to_key)
                to_emails = last_line.split(",")
                break

            iterator += 1
            all_to_emails.append("<" + email + ">" + _line_delim)
    
    return all_to_emails

#method for generating a dictionary formatted the appropriate way to send to the server
def get_email():
    email_lines = {_from_key: [], 
                    _to_key: [], 
                    _subject_key: [], 
                    _message_key: [_line_delim]}

    last_line = get_from_email()   
    #append the brackets
    email_lines[_from_key].append(last_line)
    
    all_to_emails = get_to_emails()
    #append all the the to emails
    for cur_to in all_to_emails:
        email_lines[_to_key].append(cur_to)
        
    #get the subject line
    last_line = raw_input(_subject_key)
    #no validation for subject 
    email_lines[_subject_key].append(last_line + _line_delim)

    #get data, first print prompt for user to type in a message
    print(_message_key)
    while(last_line != _end):
        last_line = raw_input()
        email_lines[_message_key].append(last_line + _line_delim)

    return email_lines

#method for generating the appropriate "DATA" message to send to the server
def get_data_string(email_lines):
    data = ""
    #only one element inside of from key
    data += _from_key + email_lines[_from_key][0]
    #iterate through all the email to recipients
    for to in email_lines[_to_key]:
        data += _to_key + to

    #only one elem in the subject key
    data += _subject_key + email_lines[_subject_key][0]
    #iterate through all the message lines
    for line in email_lines[_message_key]:
        data += line

    return data

#method for sending the smtp message to the server
def send_smtp(cmds, socket):
   
    #0 position in cmd holds key, 1 position holds value
    for cur in cmds:
        socket.send(cur[1].encode())
        #if the current command is quit, simply return, no validation needed
        if(cur[0] == _quit):
            return True
        #only wait for response if we are sending commands that arent the entire message
        #or wait for response if we just sent the ".\n" line of the message 
        elif(cur[0] != _message_key or (cur[0] == _message_key and cur[1] == (_end + _line_delim))):
            response = socket.recv(1024).decode()
            #if the response is bad, return False, which will close the connection
            if(process_response(response, cur[0]) == -1):
                return False
  
    #we never sent a quit command
    print _no_quit
    return False

#method for handling the client/server helo exchanges
def handle_helo_exchanges(clientSocket):
    
    #get client hostname
    client_hostname = getfqdn()
    #recieve welcome message
    welcome_message = clientSocket.recv(1024).decode()
    #make sure welcome message starts with 220
    if(welcome_message.split(None, 1)[0] != _helo_response):
        print _unacceptable_helo
        return False
    
    #otherwise send the HELO
    helo = _client_HELO + client_hostname + _line_delim
    clientSocket.send(helo.encode())

    #wait for rcpt of ACK
    helo_ack = clientSocket.recv(1024).decode()
    if(not helo_ack_check(helo_ack)):
        print _unacceptable_helo_ack
        return False
    
    return True

#method for verifying the server domain/hostname
def valid_server_host(hostname):
    #check to see if its a valid domain
    if(validate_domain(hostname, 0) == -1):
        return False
    return True

#method for quitting
def not_success(clientSocket):
    print _closing_connection
    clientSocket.close()
    return -1 

#initial socket setup method
def init_client_socket():
    #we forgot a param if there are less than 3 args
    if(len(sys.argv) > 2):

        #first get the email message from the client
        email_lines = get_email()
        if(email_lines == -1):
            return -1

        data = get_data_string(email_lines)
        smtp_cmds = generate_smtp_commands(data, email_lines)
        
        #get server credentials
        server_hostname = sys.argv[1]
        server_port = int(sys.argv[2])
        clientSocket = socket(AF_INET, SOCK_STREAM)
        
        #validate server hostname
        if(not valid_server_host(server_hostname)):
            print _invalid_server_hostname
            return -1
        
        #validate server/port connection
        try:
            clientSocket.connect((server_hostname, server_port))
        except:
            print _server_port_connection_error
            return -1
        
        #put try around main code to handle socket errors mid connection
        try:
            #initiate the helo message exchanges
            success = handle_helo_exchanges(clientSocket)
            if(not success):
                return not_success(clientSocket)
                        
            success = send_smtp(smtp_cmds, clientSocket)
            #if we got a False return,. something went wrong, we should close the connection
            if(not success):
                return not_success(clientSocket)
    
            #if we get to this point, we sucessfully sent the message
            clientSocket.close()
            
        except:
            print _socket_error 
            print _closing_connection
            return -1
            
    else:
        print _missing_arg
    return 1

def main():
    init_client_socket()
    return 1

main()
