import json
import requests
import collections
import config, secrets
from requests.auth import HTTPBasicAuth
from discord import Webhook, SyncWebhook

secrets = secrets.secrets
config = config.config

WEBHOOK_URL = secrets['WEBHOOK_URL']
CLIENT_ID = secrets['CLIENT_ID']
CLIENT_SECRET = secrets['CLIENT_SECRET']
API_PREFIX = config['API_PREFIX']
#Following values are retrieved using Postman Requests
FINKLE_ID =  config['FINKLE_ID']
IRONFOE_ID = config['IRONFOE_ID']
SULFURON_ID = config['SULFURON_ID']
DYNAMIC_CLASSIC_WOTLK_NAMESPACE = config['DYNAMIC_CLASSIC_WOTLK_NAMESPACE']
STATIC_CLASSIC_WOTLK_NAMESPACE = config['STATIC_CLASSIC_WOTLK_NAMESPACE']
DYNAMIC_CLASSIC_ERA_NAMESPACE = config['DYNAMIC_CLASSIC_ERA_NAMESPACE']
STATIC_CLASSIC_ERA_NAMESPACE = config['STATIC_CLASSIC_ERA_NAMESPACE']
HORDE_AUCTION_HOUSE_ID = config['HORDE_AUCTION_HOUSE_ID']
######################################################
SEARCHED_ITEMS = config['SEARCHED_ITEMS']
MAX_AUCTIONS_RETURNED = config['MAX_AUCTIONS_RETURNED']

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
				if auction['buyout']/auction['quantity'] < item['max_price'] * 10000 and auction['buyout'] > 0:
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
	introMessage = "***## De bonnes affaires potentielles en ce moment à l'HV: ##***"
	discordMessages.append(introMessage)
	result = collections.defaultdict(list)
	for matchingAuction in matching_auctions:
		result[matchingAuction['item_id']].append(matchingAuction)
	sortedAuctions= list(result.values())
	for auctions in sortedAuctions:
		item_id_message = "*# "+getItemName(access_token, auctions[0]['item_id'])+" #*\r\n"
		for index, auction in enumerate(auctions[:MAX_AUCTIONS_RETURNED]):
			item_id_message += str(index + 1) + ": enchère prix unitaire: "+setBoldDiscord(str(round(auction['unit_bid_price'], 2)) + " PO")+" PO | achat imm. prix unitaire: "+setBoldDiscord(str(round(auction['unit_buyout_price'], 2)) + " PO")
			item_id_message += " | enchère prix global: "+setBoldDiscord(str(round(auction['bid_price'], 2)) + " PO")+" | achat imm. prix global: "+setBoldDiscord(str(round(auction['buyout_price'], 2)) + " PO")
			item_id_message += " | quantité: "+setBoldDiscord(str(auction['quantity']))+" | temps restant: "+setBoldDiscord(str(auction['time_left']))
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