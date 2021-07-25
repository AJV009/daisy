from dotenv import load_dotenv
import os
import re
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import openai
import asyncio
import motor.motor_asyncio

load_dotenv()

app = AsyncApp(token=os.getenv("SLACK_BOT_TOKEN"))
openai.api_key = os.getenv("OPENAI_API_KEY")

"""
TODO:
- Collect more data from Slack weekend fun activity and store in classify.json.
"""


@app.event('app_mention')
async def app_mention(event):
    """
    Event handler for app mention.
    Then adds the channel and event_ts to the public_event_logs.
    If it starts with '@daisy Weekend fun:' categorize the message with 'weekend'.
    """
    if re.sub(r'<[^<]+?>', '', event['text'].lower()).strip().startswith('weekend fun'):
        db = await mongo_main()
        db.public_event_logs.insert_one(
            {'channel_id': event['channel'], 'message_ts': event['event_ts'], 'category': 'weekend'})


@app.event("message")
async def message(body, logger):
    """
    Event handler for message.
    And check if the message is a thread.
    * Weekend Fun:
        If it is, send the message to the emojifier and add the reaction.
    * More uses to be added.
    """
    if "thread_ts" in body["event"]:
        db = await mongo_main()
        if (await db.public_event_logs.find_one({"channel_id": body['event']['channel'], "message_ts": body['event']['thread_ts'], "category": "weekend"})):
            em = emojifier(body["event"]['text'])
            if em != False:
                await app.client.reactions_add(
                    channel=body["event"]["channel"], name=em, timestamp=body["event"]["ts"])
            else:
                db.weekend_text_log.insert_one({"message":body["event"]['text']})


def emojifier(query_val):
    """
    Function to get the emoji for the given query using OpenAI API (GPT3) text classification trained on classify.json.
    """
    label_emmoji = {"funny": 'sweat_smile', "very_funny": 'joy',
                    "funniest": 'rolling_on_the_floor_laughing'}
    try:
        response = openai.Classification.create(query=query_val,  file=os.getenv(
            "WEEKEND_CLASSIFY_FILE"), search_model="ada", model="ada", labels=['funny', 'very_funny', 'funniest'], max_examples=3)
        return label_emmoji[response.label.lower()]
    except:
        return False


async def mongo_main():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        os.getenv("MONGODB_CONNECTION_STRING"), serverSelectionTimeoutMS=5000)
    return client.daisy_slack


async def slack_main():
    handler = AsyncSocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    await handler.start_async()

if __name__ == "__main__":
    asyncio.run(slack_main())
