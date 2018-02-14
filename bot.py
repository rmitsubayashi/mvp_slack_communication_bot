# coding: utf8
import random
from slackclient import SlackClient

#since this is only a prototype,
# it is very badly coded :P

# instantiate Slack client
# IF RELEASING, MAKE SURE THIS KEY IS HIDDEN FROM THE USER!!!
slack_client = SlackClient("xoxb-313654212789-UFOpwtmq4kdJJa4z36rHo7ni")
random_channel_id = None

# constants
SECONDS_BETWEEN_NEW_POST = 86400 #so we can see an update every day
SECONDS_BETWEEN_CRON_JOB = 86400 #whatever we set the cron job to (daily atm)
DB_FILE_NAME = "timer.txt" #the local file we use as a database

def get_new_messages_from_random_channel(from_timestamp):
    #since the bot's scope doesn't allow reading channel history,
    # user the OAuth token instead
    messages_call = slack_client.api_call("channels.history",
        token="xoxp-11452837862-299598727446-313533575890-253303b56b4ce0810c57e45879566ac1",
        channel=random_channel_id,
        oldest=from_timestamp
    )
    if messages_call.get("ok") :
        messages = messages_call.get("messages")
        #we want to remove all non-messages
        messages_copy = messages[:]
        for message in messages_copy :
                if message.get("type") != "message" :
                    messages.remove(message)
        return messages

    else :
        print(messages_call.get("error"))
    return None


def get_latest_message_timestamp(from_timestamp, messages):
    if not messages :
        return from_timestamp

    latest_timestamp = ""
    for message in messages :
        if message.get("ts") > latest_timestamp :
            latest_timestamp = message.get("ts")

    return latest_timestamp

def is_a_message_from_random_channel(slack_events):
    # only checks messages from the default random channel
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event: #check if message
            print(event["channel"])
            if event["channel"] == random_channel_id: #check if from the random channel
                return True

    return False

def get_random_channel_id():
    channels_call = slack_client.api_call("channels.list", exclude_archived=1)
    if channels_call.get("ok"):
        channels = channels_call.get("channels")
        for channel in channels :
            if channel.get("name") == "random":
                return channel.get("id")

    return None

def send_message():
    message = choose_message()
    slack_client.api_call(
        "chat.postMessage",
        channel="#random",
        text=message or u"今日は何について話そうか？"
    )

def choose_message():
    message = get_random_message()
    user_id = get_random_user_id()
    user_link_string = get_user_link_string(user_id)
    return user_link_string + " " + message

def get_random_message():
    messages = [u"最近何を食べましたか？",u"出身地はどこですか？",u"最近何か買い物をしましたか？",u"今週末の予定はありますか？",u"先週末、何をしましたか？",u"通勤はどんな感じですか？"]
    return random.choice(messages)

def get_random_user_id():
    users_call = slack_client.api_call("users.list")
    if users_call.get("ok"):
        users = users_call.get("members")
        filter_out_non_user_ids(users)
        return random.choice(users).get("id")
    else :
        return None

def filter_out_non_user_ids(users):
    users_copy = users[:]
    for user in users_copy :
        if not is_active_user(user) :
            users.remove(user)

def is_active_user(user):
    if user.get("is_bot"):
        return False

    if user.get("deleted"):
        return False

    if user.get("id") == "USLACKBOT":
        return False

    return True


def get_user_link_string(user_id):
    if not user_id:
        return "";
    else :
        return "<@" + user_id + ">"

def read_current_value():
    file = open(DB_FILE_NAME, "r")
    value = int(file.readline())
    timestamp = file.readline()

    return value, timestamp

def set_current_value(value, timestamp):
    file = open(DB_FILE_NAME, "w")
    file.truncate()
    lines = str(value) + "\n" + str(timestamp)
    file.writelines(lines)
    file.close()


if __name__ == "__main__":

    # we require the user to have a random channel
    random_channel_id = get_random_channel_id()
    if not random_channel_id :
        print("Please set up a 'random' channel")

    counter, timestamp = read_current_value()
    new_messages = get_new_messages_from_random_channel(timestamp)
    #if we have a new message
    if new_messages and len(new_messages) > 0:
        #reset counter
        counter = SECONDS_BETWEEN_NEW_POST
    counter -= SECONDS_BETWEEN_CRON_JOB
    print("decrementing counter" + str(counter))
    if counter <= 0 :
        print("sending new message")
        #we should send another message
        send_message()
        #reset counter
        counter = SECONDS_BETWEEN_NEW_POST
    new_timestamp = get_latest_message_timestamp(timestamp, new_messages)
    set_current_value(counter, new_timestamp)


