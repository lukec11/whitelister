# Luke Carapezza
# Jan 04, 2019
# TODO: Improve so that it will re-run and ensure success after recieving server warning.

import slack
import paramiko
import json
from datetime import datetime
import time
import requests
import os
import base64


# Write SSH key to file so it can read it

# get info from config
config = os.environ
host = config["host"]  # hostname for vanilla server
username = config["username"]  # username for ssh server

keypass = config["keypass"]  # pass to privkey
log2 = config["logFile"]  # log file for the second server
slackToken = config["slackToken"]  # slack OAuth Bot User Token
slackChannel = config["slackChannel"]  # Slack channel (plaintext)
slackChannelId = config["slackChannelId"]  # Slack channel (CCXXXXXXXXX)
triggerWord = config["triggerWord"]  # trigger word to activate the bot

# Gets ssh key from environment, decodes base64 to bytestring, spits out utf-8
keyString = (base64.b64decode(os.environ['sshkey'])).decode('utf-8')

# Warning: shit code ahead because stringIO didn't work
with open('id_rsa', 'w') as f:  # Writes keyString to file
    f.write(keyString)
with open('id_rsa', 'r') as f:  # Reads keyString from file and sets it as the ssh key
    key = paramiko.RSAKey.from_private_key(f)


slack_client = slack.WebClient(token=slackToken)


def slackResponse(message, ts):
    slack_client.chat_postMessage(
        token=slackToken,
        as_user=False,
        channel=slackChannel,
        text=message,
        thread_ts=ts
    )


def sendSlackEmote(emote, ts):
    slack_client.reactions_add(
        token=slackToken,
        channel=slackChannelId,
        name=emote,
        timestamp=ts
    )


def vanilla(ign, ts):
    # init ssh connection
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(hostname=host, username=username, pkey=key)

    # run command to whitelist
    s.exec_command(f"tmux send-keys -t server 'whitelist add {ign}' Enter")

    # call method to check whether or not the command worked properly
    checksuccess(s, ign, log2, ts, 'vanilla')

    # close ssh connection
    s.close()


def checksuccess(s, ign, log, ts, version):
    # signature

    # check for presence in log - was the command successful?
    command = (f"tail -1 {log}")
    (stdin, stdout, stderr) = s.exec_command(command)

    # decodes output of the command
    output = stdout.read().decode("utf-8")

    # checks to ensure that the player was whitelisted, and send response in slack
    if "to the whitelist" in output:
        print(f"{ign} added to vanila server.")
        sendSlackEmote('heavy_check_mark', ts)
    elif "already whitelisted" in output:
        print(f'{ign} already whitelisted!')
        sendSlackEmote('grey_exclamation', ts)
        slackResponse('Player is already whitelisted!', ts)
    elif "does not exist" in output:
        print(f'{ign} does not exist!')
        sendSlackEmote('x', ts)
        slackResponse('That player doesn\'t exist!', ts)
    else:
        slackResponse(
            f'Error! Please check manually. Timestamp {datetime.now().strftime("%H:%M:%S")}. The latest line in the file was ```{output}```.', ts)


@ slack.RTMClient.run_on(event="message")
def message_on(**payload):
    ts = payload['data']['ts']
    try:
        data = payload['data']['blocks'][0]['elements'][0]['elements'][0]['text']
        web_client = payload['web_client']
        channel = payload['data']['channel']

        if data.startswith(triggerWord) and channel == slackChannelId:
            vanilla(data[len(triggerWord)+1: len(data)], ts)
    except KeyError as e:
        print(f'ERROR: {e}')


# verification stuff for slack
slack_token = slackToken
rtm_client = slack.RTMClient(token=slack_token)
rtm_client.start()
