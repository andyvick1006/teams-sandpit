import requests
import json
import os
from flask import Flask, render_template, request

# Init Flask
app = Flask(__name__)

# Helpers
def _url(path):
    return 'https://api.ciscospark.com/v1' + path

def _fix_at(at):
    if 'Bearer' not in at:
        return 'Bearer ' + at
    else:
        return at
        
# pySpark

def get_message(at, messageId):
    headers = {'Authorization': _fix_at(at)}
    resp = requests.get(_url('/messages/{:s}'.format(messageId)), headers=headers)
    message_dict = json.loads(resp.text)
    message_dict['statuscode'] = str(resp.status_code)
    return message_dict

def post_message_markdown(at, text, roomId='', toPersonId='', toPersonEmail=''):
    headers = {'Authorization': _fix_at(at), 'content-type': 'application/json'}
    payload = {'markdown': text}
    if roomId:
        payload['roomId'] = roomId
    if toPersonId:
        payload['toPersonId'] = toPersonId
    if toPersonEmail:
        payload['toPersonEmail'] = toPersonEmail
    images_dict = { 'AV' : 'http://web-server.caaspilot.com/hongkong.jpg'}
    if 'Unknown' in text and 'AV' in text:
        payload['files'] = images_dict['AV']
    resp = requests.post(url=_url('/messages'), json=payload, headers=headers)
    message_dict = json.loads(resp.text)
    message_dict['statuscode'] = str(resp.status_code)
    return message_dict

        
# Bot functionality 
def price(input):
    url = 'https://api.iextrading.com/1.0/stock/'+input+'/company'
    company_req = requests.get(url)
    if 'Unknown' in company_req.text :
        text = 'The stock symbol '+input+' is Unknown'
    else :
        company_dict = company_req.json()
        company = company_dict.get('companyName')
        url = 'https://api.iextrading.com/1.0/stock/'+input+'/ohlc'
        price_range = requests.get(url)
        price_range_dict = price_range.json()
        open_price_dict = price_range_dict.get('open')
        open_price = '$'+str(open_price_dict.get('price'))
        high_price = '$'+str(price_range_dict.get('high'))
        if 'None' in high_price :
            high_price = 'Market Closed'
        low_price = '$'+str(price_range_dict.get('low'))
        if 'None' in low_price :
            low_price = 'Market Closed'
        url = 'https://api.iextrading.com/1.0/stock/'+input+'/price'
        price_req = requests.get(url)
        text = '**Stock price for '+company+'**  \n- Opening : '+open_price+'  \n- Current : $'+price_req.text+'  \n- High : '+high_price+'  \n- Low : '+low_price
    return text
    
def help():
    text = "Help!! I am a stock price BOT. I will pull live prices for any stock symbol."
    return text
    
def listen(input):
    if input.lower() == 'help':
        return help()
    else:
        return price(input)

"""
ENTRY FUNCTION FOR HEROKU
"""

@app.route('/', methods=['GET'])
def landing():
    return render_template('home.html')
#    return '<html><body><h1>Hello World</h1></body></html>'

@app.route('/', methods=['POST'])
def main():

    username = os.environ.get('SPARK_BOT_USERNAME')
    #print("Username from environment: {}".format(username))
    
    at = os.environ.get('SPARK_BOT_AUTH_TOKEN')
    #print("auth: {}".format(at))
    # Get input info
    json_file = request.json
    resource = json_file['resource']
    event = json_file['event']
    data = json_file['data']

    # Check if the message came from the bot, if so, ignore
    person = data.get('personEmail')
    if '@webex.bot' not in username:
        bot_name = username + '@webex.bot'
    else:
        bot_name = username
    if person == bot_name:
        return 'heroku done', 200
    
    # Get message contents
    msg_id = data.get('id')
    msg_dict = get_message(at, msg_id)
    #Parse the text
    input = msg_dict.get('text')
    if 'av-stockticker' in input :
        x,input = input.split(' ')
    if input: 
        text = listen(input)
    else:
        return 'heroku done', 200
    
    # Get room information to send back to room the response
    #Parse the roomId
    room_id = data.get('roomId')
    
    # Send the spark message
    
    msg_dict = post_message_markdown(at, text, room_id)
    return msg_dict['statuscode']
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
