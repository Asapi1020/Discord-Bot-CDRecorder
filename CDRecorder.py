import re
import requests
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


ServerHost = "http://133.18.226.155"
port = ["8080", "8081"]
port_game = ["7777", "7778"]
user = ""
pw = ""
token = ''
KFPath = 'C:\Program Files (x86)\Steam\steamapps\common\killingfloor2'
ChromePath = 'D:\Downloads\ChromeDriver\chromedriver.exe'

EmbedColor = 0x00ff00
test_id = 829966311416528947
rec_id = 1013339698636263474
Icon_Commando = "<:Commando:836879577081970759>"
Icon_Gunslinger = "<:Gunslinger:836880150628139028>"
Icon_Sharpshooter = "<:Sharpshooter:836880168182087681>"
Icon_Medic = "<:Medic:836879698528436235>"
Icon_Support = "<:Support:836879667524403220>"
Icon_Swat = "<:SWAT:836880199014154270>"

FinderPage = "https://www.steamidfinder.com"
WikiPage = "https://wiki.killingfloor2.com"
UnknownThumbnail = "https://steamuserimages-a.akamaihd.net/ugc/1618471679321736815/B4564FF8B4F8884EA178A11E15D508286EEB04FA/?imw=5000&imh=5000&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=false"

# prepare to get map info
f = open(KFPath + '\KFGame\Localization\INT\KFGame.int', 'r', encoding='UTF-16')
datalist = f.readlines()
print("Read: KFGame.int")
f.close()

f = open('CD_CustomMapInfo.ini', 'r', encoding='UTF-8')
CD_CMI = f.readlines()
print("Read: CD_CustomMapInfo.ini")
f.close()


# Web scraping
def ExtractWeb(url, selector):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    elems = soup.select(selector)
    return elems[0]


def GetUserName(ID):
    ID3 = "U:" + str(ID%2) + ":" + str(ID)
    url = FinderPage + "/lookup/U%3A" + str(ID%2) + "%3A" + str(ID) + "/"
    selector = 'body > div.container.wrapper > div.row > div.content.col-md-12 > div > div.col-md-12.header > div > h1 > a'
    name = ExtractWeb(url, selector).contents[0].replace(" Steam ID", "")
    return name



# Map Info Handler
def GetDisplayName(mapname):
    for i in range(len(datalist)-1):
        if len(datalist[i].lower().split(mapname)) == 2:
            nextline = datalist[i+1].split("DisplayName=")
            if len(nextline) == 2:
                return nextline[1].replace('"', '').replace("\n", "")

    return mapname


def GetThumbnail(mapname, map_soup):
    elem = map_soup.find(title=re.compile(mapname))
    if(elem == None):
        return UnknownThumbnail
    
    return WikiPage + elem.contents[0].attrs["src"]


def GetCustomMapInfo(mapname):
    info = [mapname, UnknownThumbnail]
    for i in range(len(CD_CMI)-2):
        if CD_CMI[i].lower().replace("\n", "") == mapname:
            info[0] = CD_CMI[i+1].replace("\n", "")
            info[1] = CD_CMI[i+2].replace("\n", "")
            break
    return info


def GetMapSoup():
    res = requests.get(WikiPage + "/index.php?title=Maps_(Killing_Floor_2)")
    soup = BeautifulSoup(res.text, "html.parser")
    return soup

# Web Admin
def LoginWebAdmin(port):
    url_login = ServerHost + ":" + port + "/ServerAdmin/"
    
    options = Options()
    options.add_argument('--headless')
    
    driver = webdriver.Chrome(executable_path=ChromePath, options=options)
    driver.get(url_login)
    driver.find_element(By.ID, "username").send_keys(user)
    driver.find_element(By.ID, "password").send_keys(pw)
    elements = driver.find_elements(By.TAG_NAME, "button")
    for element in elements:
        if element.get_attribute("type"):
            element.send_keys(Keys.ENTER)
            break
    print("Connected: WebAdmin")
    return driver


def ReferenceBoard(driver, port):    
    # move to Stats Board
    url_board = ServerHost + ":" + port + "/ServerAdmin/current/xStatsBoard"
    driver.get(url_board)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # extract data
    selector = '#settings > tbody'
    element = soup.select(selector)
    records = []
    
    for content in element[0].contents:
        s = str(content)
        if len(s.split("KF-")) > 1:
            data = s.split("<td>")
            record = []
            for i in range(len(data)):
                datum = data[i].split("</td>")
                
                if len(datum) > 1:
                    record.append(datum[0])
            records.append(record)

    return(records)


def ReferenceCurrent(driver, port):
    # [0:ServerName, 1:IP+Map+Wave, 2:CDInfo, 3:PlayersNum, 4:Players, 5:SpectatorsNum, 6:Spectators, 7:MapURL]
    info_list = ["", "", "", "", "", "", "", ""]
    players_list = []
    spectators_list = []
    
    url = ServerHost + ":" + port + "/ServerAdmin/current/xCDInfo"
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Current Info
    info_list[0] = soup.select('#servername')[0].contents[0]

    mapname = soup.select('#mapname')[0].contents[0]
    mapname = GetDisplayName(mapname.lower())
    if mapname[:3] == "kf-":
        custommapinfo = GetCustomMapInfo(mapname)
        mapname = custommapinfo[0]
        info_list[7] = custommapinfo[1]
    else:
        info_list[7] = GetThumbnail(mapname, GetMapSoup())
        
    info_list[1] = "**MAP** " + mapname

    info_list[1] += "\n**Wave** " + soup.select('#wavenum')[0].contents[0]

    # CD Info
    info_list[2] = "MaxMonsters=" + soup.select('#cd_mm')[0].contents[0]
    info_list[2] += "\nCohortSize=" + soup.select('#cd_cs')[0].contents[0]
    info_list[2] += "\nWaveSizeFakes=" + soup.select('#cd_wsf')[0].contents[0]
    info_list[2] += "\nSpawnMod=" + soup.select('#cd_sm')[0].contents[0]
    info_list[2] += "\nSpawnPoll=" + soup.select('#cd_sp')[0].contents[0]
    info_list[2] += "\nSpawnCycle=" + soup.select('#cd_sc')[0].contents[0]

    # Players
    info_list[3] = soup.select('#playersnum')[0].contents[0]

    if info_list[3][8] != "0":
        # extract
        elem = soup.select('#players > tbody')
        for content in elem[0].contents:
            s = str(content)
            data = s.split("<td>")
            player = []
            for i in range(len(data)):
                datum = data[i].split("</td>")
                if len(datum) > 1:
                    player.append(datum[0])
            players_list.append(player)

        # sort
        sort_list=["", "", "", "", "", "", ""]
        for player in players_list:
            match player[1]:
                case "Commando":
                    info = Icon_Commando
                    priority = 0
                case "Gunslinger":
                    info = Icon_Gunslinger
                    priority = 1
                case "Sharpshooter":
                    info = Icon_Sharpshooter
                    priority = 2
                case "FieldMedic":
                    info = Icon_Medic
                    priority = 5
                case "Support":
                    info = Icon_Support
                    priority = 3
                case "SWAT":
                    info = Icon_Swat
                    priority = 4
                case _:
                    info = "?"
                    priority = 6

            info += " " + GetUserName(int(player[2]))
            sort_list[priority] += info + "\n"

        # register
        for i in range(len(sort_list)):
            if sort_list[i] != "":
                info_list[4] += sort_list[i]
        info_list[4] = info_list[4][:len(info_list[4])-1]
    else:
        info_list[4] = "No Players"

    # Spectators
    info_list[5] = soup.select('#spectatorsnum')[0].contents[0]

    if info_list[5][11] != "0":
        elem = soup.select('#spectators > tbody')
        for content in elem[0].contents:
            s = str(content)
            data = s.split("<td>")
            spectator = []
            for i in range(len(data)):
                datum = data[i].split("</td>")
                if len(datum) > 1:
                    spectator.append(datum[0])
            if len(spectator) > 1:
                info_list[6] += GetUserName(int(spectator[1])) + "\n"
        info_list[6] = info_list[6][:len(info_list[6])-1]
    else:
        info_list[6] = "No Spectators"

    return info_list
    

# discord Setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
driver = LoginWebAdmin(port[0])



# Send Embeds
async def SendRec(record, map_soup):
    # CD Info
    info = "MaxMonsters=" + record[2]
    if len(record[3]) > 1:
        info += record[3][:len(record[3])-1].replace("?","\n")
    name_map = GetDisplayName(record[0].lower())
    
    if name_map[:3] == "kf-":
        custom_map_info = GetCustomMapInfo(name_map)
        name_map = custom_map_info[0]
        url_map = custom_map_info[1]
    else:
        url_map = GetThumbnail(name_map, map_soup)
    
    embed = discord.Embed(
        title = name_map,
        color = EmbedColor,
        description = info
        )

    embed.set_thumbnail(url = url_map)

    # Players Info
    info_list = ["", "", "", "", "", "", ""]

    for i in range(4, len(record)):
        player_info = record[i].split(" : ")

        match player_info[1]:
            case "Com":
                info = Icon_Commando
                priority = 0

            case "GS":
                info = Icon_Gunslinger
                priority = 1

            case "SS":
                info = Icon_Sharpshooter
                priority = 2

            case "Med":
                info = Icon_Medic
                priority = 5

            case "Sup":
                info = Icon_Support
                priority = 3

            case "Swat":
                info = Icon_Swat
                priority = 4

            case _:
                info = '?'
                priority = 6

        info += " " + GetUserName(int(player_info[0]))
        info_list[priority] += info + "\n"
            
    name_field = "Players " + str(len(record)-4) + "/6"


    info = ""
    for i in range(len(info_list)):
        if info_list[i] != "":
            info += info_list[i]
    info = info[:len(info)-1]
        
    embed.add_field(name = name_field, value = info)

    # Select a channel    
    if record[1] == "doom_v2_plus_rmk":
        name_channel = "doom_v2_plus"        
        
    elif record[1] == "dtf_v1":
        name_channel = "dtf_pm"

    elif record[1] == "osffi_v1_ms":
        name_channel = "osffi_v1"

    else:
        name_channel = record[1]

    embed.set_author(name=record[1])
    
    for channel in client.get_all_channels():
        if channel.name == name_channel:
            await channel.send(embed = embed)
            return

    channel = client.get_channel(rec_id)
    await channel.send(embed = embed)


async def SendInfo(info_list, channel):
    embed = discord.Embed(
        title = info_list[0],
        color = EmbedColor,
        description = info_list[1]
        )

    embed.add_field(name = "Info", value = info_list[2], inline=True)
    embed.add_field(name = info_list[3], value = info_list[4], inline=True)
    embed.add_field(name = info_list[5], value = info_list[6], inline=True)

    embed.set_image(url = info_list[7])

    await channel.send(embed = embed)


# File Control
def SaveLog(port, record):
    name_file = 'CD_Record_' + port + '.log'
    f = open(name_file, 'w', encoding='UTF-8')
    f.writelines(record)
    f.close()
    print("Saved: " + name_file)

def CheckLog(port, records):
    name_file = 'CD_Record_' + port + '.log'
    f = open(name_file, 'r', encoding='UTF-8')
    log = f.read()
    f.close()
    print("Read: " + name_file)

    for i in range(len(records)):
        record = ""
        for info in records[i]:
            record += info
        if record == log:
            return i+1

    return 0


# Main Functions
async def ReloadRecord(channel):

    # Reference New Records
    count = 0
    for each_port in port:
        records = ReferenceBoard(driver, each_port)
        idx = CheckLog(each_port, records)
        
        temp_count = len(records) - idx
        count += temp_count
        
        for i in range(idx, len(records)):
            await SendRec(records[i], GetMapSoup())

        if temp_count > 0:
            SaveLog(each_port, records[len(records) - 1])

        else:
            print("Port=" + each_port + ": the latest condition")

    # Complete Message on Discord
    if count == 0:
        msg = "Already the latest condition."
    else:
        msg = str(count) + " record"
        if count == 1:
            msg += " has"
        else:
            msg += "s have"
        msg += " been updated."
    
    await channel.send(msg)


async def ShowServer(channel):
    for i in range(len(port)):
        info_list = ReferenceCurrent(driver, port[i])
        IP = ServerHost.replace("http://", "") + ":" + port_game[i]
        info_list[1] = "**IP** " + IP + "\n" + info_list[1]
        await SendInfo(info_list, channel)


# Client
@client.event
async def on_ready():
    print("Connected: Discord")
    await client.get_channel(test_id).send("Connected")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    msg = message.content.split(" ")
    
    match msg[0]:
        case "!cdrec":
            await message.channel.send("Now Loading...")
            await ReloadRecord(message.channel)
        case "!cdnow":
            await message.channel.send("Now Loading...")
            await ShowServer(message.channel)

client.run(token)
