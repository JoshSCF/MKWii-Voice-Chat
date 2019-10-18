import discord, asyncio, json, time, random
from requests_html import HTMLSession

Token = "xxx" # Bot token here

Session = HTMLSession()
client = discord.Client()

removable = """friend code
role
login
region
room,
match
world
connfail
versus
points
battle
points
Mii name"""

ShortNames = {
	"Worldwide": "ww",
	"Continental": "cn",
	"Private": "pv",
	"Global": "gl",
	"Battle": "ba"
}

Commands = """`!help, !cmds, !commmands`: Lists all commands available to members.
`!whois xxxx-xxxx-xxxx`: Returns the Discord user attached to the specified friend code.
`!setup`: Allows you to connect a new friend code to your account.
"""

CurrentChannels = []
CurrentCodes = {}
Server = ""

def OpenFile():
	Data = open("data.json", "r")
	ActualData = Data.read()
	Data.close()
	return json.loads(ActualData)

def EditFile(FriendCode, DiscordID):
	Data = open("data.json", "r+")
	ActualData = json.loads(Data.read())
	ActualData[FriendCode] = DiscordID
	Data.close()
	NewData = open("data.json", "w")
	NewData.write(json.dumps(ActualData))
	NewData.close()
	print(FriendCode + " verified!")

def CheckChannel(ChannelName, Servers):
	for i in Servers:
		if i["Name"] == ChannelName:
			return True
	return False

async def CheckSite(FriendCode):
	global removable, ShortNames, CurrentChannels, Server, CurrentCodes
	Servers = []
	try:
		Site = Session.get("https://wiimmfi.de/mkw")
		for i in Site.html.find('tr'):
			#print(i.text)
			if i.text != removable:
				#print(i.text, "-------------------------------------", sep="\n")
				if i.text.split()[0] in ShortNames:
					Servers.append({
						"Name": ShortNames[i.text.split()[0]] + "-" + i.text.split()[2],
						"Players": {}
					})
				else:
					if len(i.text.split("\n")) >= 9:
						Servers[len(Servers) - 1]["Players"][i.text.split("\n")[0]] = " ".join(i.text.split("\n")[8:]).replace("1. ", "").replace("2. ", "")
					else:
						Servers[len(Servers) - 1]["Players"][i.text.split("\n")[0]] = "Unnamed"
	except Exception as e: print(e)

	for i in Servers:
		#print(i["Name"])
		try:
			CurrentData = OpenFile()
			if i["Name"] not in CurrentChannels:
				CurrentChannels.append(i["Name"])
				Perm = discord.ChannelPermissions(target=Server.default_role, overwrite=discord.PermissionOverwrite(connect=False))
				await client.create_channel(Server, i["Name"], Perm, type=discord.ChannelType.voice)
			for x in i["Players"]:
				if x == FriendCode:
					return i["Players"][x]
				try:
					Member = Server.get_member(CurrentData[x])
					Channel = discord.utils.get(Server.channels, name=i["Name"], type=discord.ChannelType.voice)
					if Member.voice.voice_channel:
						if Member not in Channel.voice_members:
							await client.move_member(Member, Channel)
							CurrentCodes[Member] = x
					NewName = [Member.name, Member.name[:16] + "..."][len(Member.name) > 16] + " | " + i["Players"][x]
					if Member.nick != NewName:
						await client.change_nickname(Member, NewName)
				except: 0
				#print("    ", x, i["Players"][x])
		except Exception as e: print(e)

	for i in CurrentChannels:
		try:
			if not CheckChannel(i, Servers):
				ChannelToDel = discord.utils.get(Server.channels, name=i, type=discord.ChannelType.voice)
				if len(ChannelToDel.voice_members) == 0:
					await client.delete_channel(ChannelToDel)
					CurrentChannels.remove(i)
				"""for x in ChannelToDel.voice_members:
					await client.move_member(x, client.get_channel("507321067321294853"))
					CurrentCodes[x] = None""" # Removed in favour of leseratte's suggestion
		except Exception as e: print(e)

	"""CurrentPlayers = []
	CurrentVoiceMembers = []
	try:
		for i in CurrentCodes:
			for x in Servers:
				for y in x["Players"]:
					if y == CurrentCodes[i]:
						CurrentPlayers.append(i)

		for i in CurrentChannels:
			Channel = discord.utils.get(Server.channels, name=i, type=discord.ChannelType.voice)
			for x in Channel.voice_members:
				CurrentVoiceMembers.append(x)
		for i in list(set(CurrentVoiceMembers)-set(CurrentPlayers)):
			print(i.nick + " disconnected.")
			await client.move_member(i, client.get_channel("507321067321294853"))
	except Exception as e: print(e)""" # removed in favour of leseratte's suggestion

async def SetupUser(member):
	Numbers = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh", "twelvth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "ninteenth", "twentieth"]
	TotalConnections = 0
	GeneratedCode = str(random.randint(1000,9999))
	await client.send_message(member, "Hey there, welcome to the MKWii Voice Chat server!\nTo use the voice chat service, please start by changing your mii name to **" + str(GeneratedCode) + "**. This will allow us to verify your FC later!\nNext, please reply with the amount of licenses that you would like to connect to the voice chat server. You should respond with a number from 1-20.\n\nIf you have already registered your friend code before, you do not need to change your Mii name. You will be automatically connected when you enter your friend code.")
	FCAmount = await client.wait_for_message(timeout = 600, author = member)
	if not FCAmount:
		await client.send_message(member, "I haven't seen a response in a while, if you would still like to setup, please type \"!setup\" to restart the process.")
		return
	FCAmount = FCAmount.content
	if FCAmount in list(map(str, range(1, 21))):
		for i in range(int(FCAmount)):
			await client.send_message(member, "Ok, please respond with the " + Numbers[i] + " friend code that you would like to connect. Your friend code is the 12-digit code that can be found on your license when you first open MKWii. You should ensure that the Mii name associated with that license is the code I gave you earlier.")
			FCMSG = await client.wait_for_message(timeout = 600, author = member)
			if FCMSG:
				FriendCode = FCMSG.content.replace("-", "").replace(" ", "")
				FriendCode = '-'.join(FriendCode[i:i+4] for i in range(0, 16, 4))[:14]
				try:
					if OpenFile()[FriendCode] == member.id:
						await client.add_roles(member, discord.utils.get(client.get_server("507321067321294848").roles, name="Connected"))
						await client.send_message(member, "Connected!")
						TotalConnections += 1
						return
				except Exception as e: print(e)
				await client.send_message(member, "Ok, thank you! To connect your license, please create a new private friend room. When you're done, just reply with any message.")
				Response = await client.wait_for_message(timeout = 600, author = member)
				FinalMessage = await client.send_message(member, "Please wait while we check Wiimmfi...")
				if Response:
					if await CheckSite(FriendCode) == GeneratedCode:
						EditFile(FriendCode, member.id)
						await client.add_roles(member, discord.utils.get(client.get_server("507321067321294848").roles, name="Connected"))
						await client.edit_message(FinalMessage, "Connected!")
						TotalConnections += 1
					else:
						await client.edit_message(FinalMessage, "Sorry, I can't seem to find you!")
				else:
					await client.send_message(member, "I haven't seen a response in a while, if you would still like to setup, please type \"!setup\" to restart the process.")
			else:
				await client.send_message(member, "I haven't seen a response in a while, if you would still like to setup, please type \"!setup\" to restart the process.")
		if TotalConnections:
			await client.send_message(member, "That's it, I've now connected you to your licenses! You may now change your mii name back.\nTo use the voice chat, join the \"Searching for a room\" channel and then simply join a room. We'll do the rest!\n\n- Don't worry about your nickname, it will be automatically changed as soon as you join a room with another mii name.\n- To setup more licenses, simply use the \"!setup\" command and I'll send you another message!")
		else:
			await client.send_message(member, "Unfortunately, I was unable to connect you to your licenses. You can use \"!setup\" to try again. If you're having issues, feel free to DM Josh for help!")
	else:
		await client.send_message(member, "That's not a valid response! You should respond with a number from 1-20. You can restart the process by using the '!setup' command.")

@client.event
async def on_member_join(member):
	await SetupUser(member)

@client.event
async def on_message(message):
	global Commands

	if message.content.startswith("!setup"):
		await SetupUser(Server.get_member(message.author.id))

	elif message.content.startswith("!whois"):
		FCMSG = message.content.split()[1]
		FriendCode = FCMSG.replace("-", "")
		FriendCode = '-'.join(FriendCode[i:i+4] for i in range(0, 16, 4))[:14]
		Data = OpenFile()

		if FriendCode in Data.keys():
			await client.send_message(message.channel, "That FC is attached to <@" + Data[FriendCode] + ">!")
		else:
			await client.send_message(message.channel, "Sorry, I don't know anyone with that FC :(")

	elif message.content.startswith("!connect"):
		if message.author.top_role.name in ["Developer", "Staff", "Wiimmfi Moderator"]:
			try:
				FC = message.content.split()[2].replace("-", "")
				if len(FC) == 12 and all(x in "1234567890" for x in FC):
					EditFile('-'.join(FC[i:i+4] for i in range(0, 16, 4))[:14], message.mentions[0].id)
					await client.add_roles(message.mentions[0], discord.utils.get(client.get_server("507321067321294848").roles, name="Connected"))
					await client.send_message(message.channel, "The user has now been connected to their Wiimmfi license.")
			except:
				await client.send_message(message.channel, "Sorry, something went wrong!")

	elif message.content.startswith("!help") or message.content.startswith("!cmds") or message.content.startswith("!commands"):
		await client.send_message(message.channel, Commands)

	elif message.content.startswith("!mute"):
		if message.author.top_role.name in ["Developer", "Staff"]:
			try:
				if message.mentions[0].top_role.name not in ["Developer", "Staff"]:
					await client.add_roles(message.mentions[0], discord.utils.get(message.server.roles, name="Muted"))
					await client.send_message(message.channel, "That user has now been muted!")
			except:
				await client.send_message(message.channel, "Sorry, something went wrong!")

	elif message.content.startswith("!unmute"):
		if message.author.top_role.name in ["Developer", "Staff"]:
			try:
				await client.remove_roles(message.mentions[0], discord.utils.get(message.server.roles, name="Muted"))
				await client.send_message(message.channel, "That user has now been unmuted!")
			except:
				await client.send_message(message.channel, "Sorry, something went wrong!")

	elif message.content.startswith("!kick"):
		if message.author.top_role.name in ["Developer", "Staff"]:
			try:
				if message.mentions[0].top_role.name not in ["Developer", "Staff"]:
					await client.kick(message.mentions[0])
					await client.send_message(message.channel, "That user has now been kicked!")
			except:
				await client.send_message(message.channel, "Sorry, something went wrong!")

@client.event
async def on_ready():
	global Server
	print("hi great news im online")
	await client.change_presence(game = discord.Game(name = "Mario Kart Wii"))
	Server = client.get_server("507321067321294848")
	Channels = Server.channels
	for i in list(Channels):
		try:
			if "ww" in i.name or "cn" in i.name or "pv" in i.name or "gl" in i.name:
				for x in i.voice_members:
					await client.move_member(x, client.get_channel("507321067321294853"))
				await client.delete_channel(i)
		except Exception as e: print(e)

	while True:
		await asyncio.sleep(6)
		await CheckSite("abc")

client.run(Token)
