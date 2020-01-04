import slack
import paramiko
import json
from datetime import datetime
import time

#get info from config
with open ("config.json") as f:
    config = json.load(f)

    hostModded = config["host"] #hostname for modded server
    hostVan = config["host2"] #hostname for vanilla server
    username = config["username"] #username for ssh server
    key = paramiko.RSAKey.from_private_key_file(config["privkey"]) #generates paramiko key from an openssh privkey
    keypass = config["keypass"] #pass to privkey
    log1 = config["log1"] #location of mc log files
    log2 = config["log2"]

def slackResponse(message):
    print(message)

def modded(ign):
    #initialize ssh connection to server
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(hostname = hostModded, username = username, pkey = key)
    
    #run command to whitelist
    s.exec_command(f"tmux send-keys -t 0 'whitelist add {ign}' Enter")

    #calls method to check whether or not the command worked
    checksuccess(s, ign, log1)
    
    #close ssh connection
    s.close()

def vanilla(ign):
    #init ssh connection
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(hostname = hostVan, username = username, pkey = key)

    #run command to whitelist
    s.exec_command(f"tmux send-keys -t 0 'whitelist add {ign}' Enter")

    #call method to check whether or not the command worked properly
    checksuccess(s, ign, log2)

    #close ssh connection
    s.close()

def checksuccess(s, ign, log):
    #signature
    signature = "Sign Server MODDED."

    #check for presence in log - was the command successful?
    command = (f"tail -1 {log}")
    (stdin, stdout, stderr) = s.exec_command(command)

    #decodes output of the command
    output = stdout.read().decode("utf-8")
    
    #checks to ensure that the player was whitelisted
    if "to the whitelist" in output:
        slackResponse(f"{ign} was added to the whitelist. {signature}")
    else:
        slackResponse(f'Error! Please check manually. Timestamp {datetime.now().strftime("%H:%M:%S")}. {signature}')
        slackResponse(f"The latest line in the file was `{output}`.")
    






