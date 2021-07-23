from dotenv import load_dotenv
import os, re
from slack_bolt import App
import openai

load_dotenv()

app =  App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)
openai.api_key = os.getenv("OPENAI_API_KEY")

"""
TODO:
- Use Flask or FastAPI to handle Slack API calls.
- Use some kind of DB to store public_event_logs.
- Collect more data from Slack weekend fun activity and store in classify.json.
"""

public_event_logs = []

@app.event('app_mention')
def app_mention(event):
    if re.sub(r'<[^<]+?>', '', event['text']).strip().startswith('Weekend fun:'):
        public_event_logs.append({'channel_id': event['channel'], 'message_ts': event['event_ts'], 'category': 'weekend'})

@app.event("message")
def message(body, logger):
    if "thread_ts" in body["event"]:
        if body["event"]["thread_ts"] in [val['message_ts'] for val in public_event_logs]:
            em = emojifier(body["event"]['text'])
            if em != False:
                app.client.reactions_add(channel=body["event"]["channel"],name=em,timestamp=body["event"]["ts"])

def emojifier(query_val):
    label_emmoji = {"funny":'sweat_smile',"very_funny":'joy',"funniest":'rolling_on_the_floor_laughing'}
    try:
        response = openai.Classification.create(query=query_val,  file=os.getenv("WEEKEND_CLASSIFY_FILE"), search_model="ada", model="ada", labels=['funny','very_funny','funniest'], max_examples=3)
        return label_emmoji[response.label.lower()]
    except:
        return False

#  Run all daisies
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT",3050)))