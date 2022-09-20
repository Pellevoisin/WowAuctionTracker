import json
import requests
import collections
from requests.auth import HTTPBasicAuth
from discord import Webhook, SyncWebhook

WEBHOOK_URL = "https://discord.com/api/webhooks/909048587042844683/l40jqfXb9QKciiHm7iqVFTjggw0uSPbuVKh_A0azty3MxgppBIktCuOqABqGJamXpw1S"
CLIENT_ID = "94b01e3ac4d54cfd8117d2f67b11bf63"
CLIENT_SECRET = "j2ITUFfObTsv0AyUe4fSByeqLSSHNYIn"
API_PREFIX = "https://eu.api.blizzard.com"
#Following values are retrieved using Postman Requests
FINKLE_ID = "4744"
IRONFOE_ID = "5265"
SULFURON_ID = "4464"
DYNAMIC_CLASSIC_WOTLK_NAMESPACE = "dynamic-classic-eu"
STATIC_CLASSIC_WOTLK_NAMESPACE = "static-classic-eu"
DYNAMIC_CLASSIC_ERA_NAMESPACE = "dynamic-classic1x-eu"
STATIC_CLASSIC_ERA_NAMESPACE = "static-classic1x-eu"
HORDE_AUCTION_HOUSE_ID = "6"
######################################################
SEARCHED_ITEMS = [
	{"item_id":"2775", "item_name":"Minerai d'argent", "max_price":15},
	{"item_id":"4369", "item_name":"Tromblon mortel", "max_price":20},
	{"item_id":"22451", "item_name":"Air primordial", "max_price":14}
]
MAX_AUCTIONS_RETURNED = 10

def setBoldDiscord(message):
	boldMessage = "***"+message+"***"
	return boldMessage

def getAccessToken(client_id, client_secret):
   URL = "https://eu.battle.net/oauth/token"
   r = requests.post(URL, data= {'grant_type' : 'client_credentials'}, auth=HTTPBasicAuth(client_id, client_secret))
   return json.loads(r.text)['access_token']

def getAuctions(access_token, realm_id, auction_house_id):
	URL = API_PREFIX+"/data/wow/connected-realm/"+realm_id+"/auctions/"+auction_house_id
	authorization = "Bearer " + access_token
	r = requests.get(URL, headers={"Authorization":authorization, "Battlenet-Namespace":DYNAMIC_CLASSIC_WOTLK_NAMESPACE})
	return json.loads(r.text)

def getIconURL(access_token, item_id):
	URL = API_PREFIX+"/data/wow/media/item/"+item_id
	authorization = "Bearer " + access_token
	r = requests.get(URL, headers={"Authorization":authorization, "Battlenet-Namespace":STATIC_CLASSIC_WOTLK_NAMESPACE})
	return json.loads(r.text)['assets'][0]['value']

def getItemName(access_token, item_id):
	URL = API_PREFIX+"/data/wow/item/"+item_id+"?locale=fr_FR"
	authorization = "Bearer " + access_token
	r = requests.get(URL, headers={"Authorization":authorization, "Battlenet-Namespace":STATIC_CLASSIC_WOTLK_NAMESPACE})
	return json.loads(r.text)['name']

def getValuableAuctions(searched_items, auctionsJSON):
	matchingAuctions = []
	for auction in auctionsJSON['auctions']:
		for item in searched_items:
			if str(auction['item']['id']) in item['item_id']:
				if auction['buyout']/auction['quantity'] < item['max_price'] * 10000:
					matchingAuction = {
						"item_id":str(auction['item']['id']), 
						"buyout_price":auction['buyout']/10000, 
						"bid_price":auction['bid']/10000,
						"unit_buyout_price":auction['buyout']/10000/auction['quantity'], 
						"unit_bid_price":auction['bid']/10000/auction['quantity'],
						"quantity":auction['quantity'],
						"time_left":auction['time_left']
					}
					matchingAuctions.append(matchingAuction)
	#Order auctions list by buyout price, ascending
	matchingAuctions = sorted(matchingAuctions, key=lambda d: d['unit_buyout_price'])
	return matchingAuctions

def renderDiscordMessages(access_token, matching_auctions):
	discordMessages = []
	introMessage = "## Some interesting auctions have been found: ##"
	discordMessages.append(introMessage)
	result = collections.defaultdict(list)
	for matchingAuction in matching_auctions:
		result[matchingAuction['item_id']].append(matchingAuction)
	sortedAuctions= list(result.values())
	for auctions in sortedAuctions:
		item_id_message = "# "+getItemName(access_token, auctions[0]['item_id'])+" #\r\n"
		for auction in auctions[:MAX_AUCTIONS_RETURNED]:
			item_id_message += "bid_price: "+setBoldDiscord(str(auction['bid_price']))+" | buyout_price: "+setBoldDiscord(str(auction['buyout_price']))
			item_id_message += " | unit_bid_price: "+setBoldDiscord(str(auction['unit_bid_price']))+" | unit_buyout_price: "+setBoldDiscord(str(auction['unit_buyout_price']))
			item_id_message += " | quantity: "+setBoldDiscord(str(auction['quantity']))+" | time_left: "+setBoldDiscord(str(auction['time_left']))
			item_id_message += "\r\n"
		discordMessages.append(item_id_message)
	return discordMessages

#####  MAIN  #####
accessToken = getAccessToken(CLIENT_ID, CLIENT_SECRET)
auctions = getAuctions(accessToken, SULFURON_ID, HORDE_AUCTION_HOUSE_ID)
matchingAuctions = getValuableAuctions(SEARCHED_ITEMS, auctions)

discordMessages = renderDiscordMessages(accessToken, matchingAuctions)
for message in discordMessages:
	if matchingAuctions is not None:
		webhook = SyncWebhook.from_url(WEBHOOK_URL)
		webhook.send(message)