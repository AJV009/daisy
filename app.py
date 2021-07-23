from dotenv import load_dotenv
import os, re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import openai

load_dotenv()

app =  App(token=os.getenv("SLACK_BOT_TOKEN"))
openai.api_key = os.getenv("OPENAI_API_KEY")

"""
TODO:
- Use some kind of DB to store public_event_logs.
- Collect more data from Slack weekend fun activity and store in classify.json.
"""

public_event_logs = []

@app.event('app_mention')
def app_mention(event):
    """
    Event handler for app mention.
    Then adds the channel and event_ts to the public_event_logs.
    If it starts with '@daisy Weekend fun:' categorize the message with 'weekend'.
    """
    if re.sub(r'<[^<]+?>', '', event['text']).strip().startswith('Weekend fun:'):
        public_event_logs.append({'channel_id': event['channel'], 'message_ts': event['event_ts'], 'category': 'weekend'})

@app.event("message")
def message(body, logger):
    """
    Event handler for message.
    And check if the message is a thread.
    * Weekend Fun:
        If it is, send the message to the emojifier and add the reaction.
    * More uses to be added.
    """
    if "thread_ts" in body["event"]:
        if body["event"]["thread_ts"] in [val['message_ts'] for val in public_event_logs]:
            em = emojifier(body["event"]['text'])
            if em != False:
                app.client.reactions_add(channel=body["event"]["channel"],name=em,timestamp=body["event"]["ts"])

def emojifier(query_val):
    """
    Function to get the emoji for the given query using OpenAI API (GPT3) text classification trained on classify.json.
    """
    label_emmoji = {"funny":'sweat_smile',"very_funny":'joy',"funniest":'rolling_on_the_floor_laughing'}
    try:
        response = openai.Classification.create(query=query_val,  file=os.getenv("WEEKEND_CLASSIFY_FILE"), search_model="ada", model="ada", labels=['funny','very_funny','funniest'], max_examples=3)
        return label_emmoji[response.label.lower()]
    except:
        return False

#  Run all Daisies
if __name__ == "__main__":
    # Websocket mode
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
