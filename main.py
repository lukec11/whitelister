#Luke Carapezza
#Jan 04, 2019
#TODO: Improve so that it will re-run and ensure success after recieving server warning.

import slack
import paramiko
import json
from datetime import datetime
import time
from airtable import Airtable
import requests


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
    slackToken = config["slackToken"]
    slackChannel = config["slackChannel"]
    slackChannelId = config["slackChannelId"]
    triggerWord = config["triggerWord"]

with open ("configStickers.json") as f:
    config = json.load(f)

    api_key1 = config['api_key']
    base_key = config['base_key']
    table_name = config['table_name']

slack_client = slack.WebClient(token = slackToken)
def slackResponse(message, ts):
    slack_client.chat_postMessage(token = slackToken, as_user=False, channel=slackChannel, text=message, thread_ts=ts)
    
def slackEmote(color, ts):
    if color == 'green':
        slack_client.reactions_add(token=slackToken, channel=slackChannelId, name="heavy_check_mark", timestamp=ts)
    elif color == 'white':
        slack_client.reactions_add(token=slackToken, channel=slackChannelId, name="white_check_mark", timestamp=ts)
    elif color == 'airtable':
        slack_client.reactions_add(token = slackToken, channel = slackChannelId, name="airtable", timestamp=ts)
    else:
        print (f"Unknown color: color was reported as \"{color}\"")

def modded(ign, ts):
    #initialize ssh connection to server
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(hostname = hostModded, username = username, pkey = key)
    
    #run command to whitelist
    s.exec_command(f"tmux send-keys -t 0 'whitelist add {ign}' Enter")

    #calls method to check whether or not the command worked
    checksuccess(s, ign, log1, ts, 'modded')
    
    #close ssh connection
    s.close()

def vanilla(ign, ts):
    #init ssh connection
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(hostname = hostVan, username = username, pkey = key)
    
    #run command to whitelist
    s.exec_command(f"tmux send-keys -t 0 'whitelist add {ign}' Enter")
    
    #call method to check whether or not the command worked properly
    checksuccess(s, ign, log2, ts, 'vanilla')

    #close ssh connection
    s.close()

def checksuccess(s, ign, log, ts, version):
    #signature
    signature = f"Sign Server {version}."

    #check for presence in log - was the command successful?
    command = (f"tail -1 {log}")
    (stdin, stdout, stderr) = s.exec_command(command)

    #decodes output of the command
    output = stdout.read().decode("utf-8")
    
    #checks to ensure that the player was whitelisted, and send response in slack
    if "to the whitelist" or "is already whitelisted" in output:
        if version == 'modded':
            slackEmote('green', ts)
            print(f"{ign} added to modded server.")
        elif version == 'vanilla':
            print(f"{ign} added to vanila server.")
            slackEmote('white', ts)
    else:
        slackResponse(f'Error! Please check manually. Timestamp {datetime.now().strftime("%H:%M:%S")}. {signature}', ts)
        slackResponse(f"The latest line in the file was `{output}`.", ts)


#stuff for airtable - stickers

def airtable():
    airtable = Airtable(base_key, table_name, api_key = api_key1 ) 
    s = json.loads(json.dumps(airtable.get_all()))

    return s

def addToAirtable(ign, ts):
    '''s = airtable()
    s.insert({'IGN', ign})
    slackEmote("airtable", ts)'''
    pass

    

@slack.RTMClient.run_on(event="message")
def message_on(**payload):
    ts = payload['data']['ts']
    try:
        data = payload['data']['text']
        web_client = payload['web_client']

        if data.startswith(triggerWord):
            modded(data[len(triggerWord)+1:len(data)], ts)
            vanilla(data[len(triggerWord)+1:len(data)], ts)
            addToAirtable(data[len(triggerWord)+1:len(data)], ts)
    except KeyError:
        print ("threaded message, ignore.")


#verification stuff for slack
slack_token = slackToken
rtm_client = slack.RTMClient(token=slack_token)
rtm_client.start()
