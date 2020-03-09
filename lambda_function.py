from twilio.twiml.messaging_response import Message, MessagingResponse

import json

def lambda_handler(event, context):
    print("Received event: " + str(event))
    resp = MessagingResponse()

    resp.message("Hello World")

    return str(resp)
