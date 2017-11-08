# simple-smtp-client-server
This was a project I worked on in my Intro to Internet Services and Protocols class. It includes a simple SMTP client and server. You can use the client in order to send emails, provided you have access to an (actual) SMTP server that has resources allocated to actually receive, process, and forward emails to the appropriate user. The server will mimic the actions of an actual SMTP server capable of forwarding emails to users. In this case, it will forward any email you send to it to a folder in the <code>forward</code> folder. 

Both the client and server validate commands, domains, hosts, and email bodies associated with the full email you are trying to send.

To send an email using the client type:

<code>python Client.py \<host\> \<port\></code>

You will then be prompted for:

<code>From:</code> type your email here then click "enter"

<code>To:</code> type who you want to send to here then click "enter"

<code>Subject:</code> give a subject line then click "enter"

<code>Message (end message by typing \<CRLF\>.\<CRLF\>):</code>
Type your message to the recipient here, you can press "enter" as many times as you want.
To complete the body of your message, on a new line, simple type "." then click the "enter" button, demonstrated on the next line.

<code>.</code>

If you want to send an email to Server.py, make sure Server.py is running and you type the host of Server.py and the same port that Server.py is running on in your initial start command to Client.py.

Run Server.py in the following manner:

<code>python Server.py \<port\></code>

messages sent to Server.py should be forwarded to <code>/forward/\<domain\></code>
