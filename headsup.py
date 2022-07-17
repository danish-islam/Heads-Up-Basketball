import discord
from discord.utils import get
from bs4 import BeautifulSoup
import requests 
import pandas as pd 
from datetime import date

import datetime
from dateutil import parser

from keepalive import keep_alive

client = discord.Client()
alert_role_made = False
message2_sent = False


def NBA_team_name(text):
    return text.split('-')[0]

def NBA_emoji(x):
    if x == 'Atlanta Hawks': return ':bird:'
    if x == 'Boston Celtics': return ':four_leaf_clover:'
    if x == 'Brooklyn Nets': return ':cityscape:'
    if x == 'Charlotte Hornets': return ':bee:'
    if x == 'Chicago Bulls': return ':ox:'
    if x == 'Cleveland Cavaliers': return ':crossed_swords'
    if x == 'Dallas Mavericks': return ':racehorse:'
    if x == 'Denver Nuggets': return ':pick:'
    if x == 'Detroit Pistons': return ':pickup_truck:'
    if x == 'Golden State Warriors': return ':bridge_at_night:'
    if x == 'Houston Rockets': return ':rocket:'
    if x == 'Indiana Pacers': return ':race_car:'
    if x == 'Los Angeles Clippers': return ':sailboat:'
    if x == 'Los Angeles Lakers': return ':sunrise:'
    if x == 'Memphis Grizzlies': return ':bear:'
    if x == 'Miami Heat': return ':fire:'
    if x == 'Milwaukee Bucks': return ':deer:'
    if x == 'Minnesota Timberwolves': return ':wolf:'
    if x == 'New Orleans Pelicans': return ':trumpet:'
    if x == 'New York Knicks': return ':statue_of_liberty:'
    if x == 'Oklahoma City Thunder': return ':zap:'
    if x == 'Orlando Magic': return ':magic_wand:'
    if x == 'Philadelphia 76ers': return ':bell:'
    if x == 'Phoenix Suns': return ':cactus:'
    if x == 'Portland Trail Blazers': return ':mountain:'
    if x == 'Sacramento Kings': return ':crown:'
    if x == 'San Antonio Spurs': return ':cowboy:'
    if x == 'Toronto Raptors': return ':dragon_face:'
    if x == 'Utah Jazz': return ':notes:'
    if x == 'Washington Wizards': return ':man_mage:'

def NBA_Eastern_Standings():
    url = 'https://www.cbssports.com/nba/standings/regular/conference/'
    page = requests.get(url)
    soup = BeautifulSoup(page.text,'lxml')
    headers = ['#','Team','Wins','Losses','%W','GB','PPG','OPPG','DIFF','HOME','ROAD','DIV','CONF','STRK','L10','W_proj','Div','Post']

    table = soup.find('table',{'class':'TableBase-table'})
    NBA_east = pd.DataFrame(columns=headers)
    for row in table.find_all('tr')[2:]:
        data = row.find_all('td')
        row_data = [td.text.strip() for td in data]
        length = len(NBA_east)
        NBA_east.loc[length] = row_data
    NBA_east = NBA_east.set_index('#')[['Team','Wins','Losses','%W','GB','STRK','L10']]

    NBA_east['Team'] = NBA_east['Team'].apply(NBA_team_name)
    return NBA_east

def NBA_Western_Standings():
    url = 'https://www.cbssports.com/nba/standings/regular/conference/'
    page = requests.get(url)
    soup = BeautifulSoup(page.text,'lxml')
    headers = ['#','Team','Wins','Losses','%W','GB','PPG','OPPG','DIFF','HOME','ROAD','DIV','CONF','STRK','L10','W_proj','Div','Post']

    table = soup.find_all('table',{'class':'TableBase-table'},limit=2)[1]
    NBA_west = pd.DataFrame(columns = headers)
    for row in table.find_all('tr')[2:]:
        data = row.find_all('td')
        row_data = [td.text.strip() for td in data]
        length = len(NBA_west)
        NBA_west.loc[length] = row_data
    NBA_west = NBA_west.set_index('#')[['Team','Wins','Losses','%W','GB','STRK','L10']]

    NBA_west['Team'] = NBA_west['Team'].apply(NBA_team_name)
    return NBA_west

def CEBL_Standings():
    url = 'https://en.wikipedia.org/wiki/2022_CEBL_season'
    page = requests.get(url)
    soup = BeautifulSoup(page.text,'lxml')
    headers_stats = ['#','Games-Played','Wins','Losses','Points For','Points Against','Point Difference','%W']
    CEBL_stats = pd.DataFrame(columns = headers_stats)
    CEBL_names = pd.DataFrame(columns = ['Team'])

    table = soup.find('table',{'class':'wikitable'})
    for row in table.find_all('tr')[1:]:
        data = row.find_all('td')
        row_data = [td.text.strip() for td in data][0:8]
        length = len(CEBL_stats)
        CEBL_stats.loc[length] = row_data
        
    for row in table.find_all('tr')[1:]:
        data = row.find_all('th')
        row_data = [td.text.strip() for td in data]
        length = len(CEBL_names)
        CEBL_names.loc[length] = row_data

    CEBL = pd.concat([CEBL_stats,CEBL_names],axis=1).set_index('#')[['Team','Wins','Losses','Games-Played','%W']]
    return CEBL

def split_CEBL_matchup(string):
    if(len(string.split('vs'))==2):
       return string.split('vs') 
    else:
        return string.split('at')

def CEBL_today():
    url = "https://www.cbc.ca/sports-content/v11/includes/json/schedules/broadcast_schedule.json"
    df = pd.DataFrame(requests.get(url).json()["schedule"])

    CEBL_game = df['ti'].apply(lambda string: string.split()[0:4]).apply(lambda array: " ".join(array)) == 'Canadian Elite Basketball League:'
    CEBL_game_table = df[CEBL_game][['stt','end','ti']]
    CEBL_game_table['Match Up'] = CEBL_game_table['ti'].apply(lambda string: string.split(":")[1])
    CEBL_game_table.drop('ti',axis=1,inplace=True)

    CEBL_game_table['date']=CEBL_game_table['stt'].apply(lambda string: string.split()[0])
    CEBL_game_table['start time']=CEBL_game_table['stt'].apply(lambda string: string.split()[1])
    CEBL_game_table['end time']=CEBL_game_table['end'].apply(lambda string: string.split()[1])

    CEBL = CEBL_game_table[['start time','end time','date','Match Up']]
    CEBL['date'].apply(lambda date: pd.to_datetime(date))
    CEBL = CEBL.reset_index().drop('index',axis=1)
    CEBL.columns = ['Start','End','Date','Match Up']
    CEBL = CEBL[['Match Up','Start','End','Date']]
    CEBL_today = CEBL[CEBL['Date'].apply(lambda date: pd.to_datetime(date).date()) == date.today()]

    CEBL_today['Home'] = CEBL_today['Match Up'].apply(split_CEBL_matchup).apply(lambda list: list[1])
    CEBL_today['Away'] = CEBL_today['Match Up'].apply(split_CEBL_matchup).apply(lambda list: list[0])
    CEBL_today = CEBL_today.drop('Match Up',axis=1)[['Home','Away','Start','End','Date']]

    CEBL_today['Home'] = CEBL_today['Home'].apply(lambda string: string.split()).apply(lambda array: array[0])
    CEBL_today['Away'] = CEBL_today['Away'].apply(lambda string: string.split()).apply(lambda array: array[0])

    return CEBL_today.reset_index().drop('index',axis=1)

def valid_announcement(message_sent,message_expected):
    current = datetime.datetime.now()
    if(message_sent == False and current.year==message_expected.year and current.month == message_expected.month and current.day==message_expected.day):
        return True
    else:
        return False

class message1:
    sent = False
    expected = parser.parse('July 17 2022')
    content = "The notifications on this bot is working!"

class message2:
    sent = False
    expected = parser.parse('October 12 2022')
    content = "The NBA season starts in a week on October 19th, 2022!"

class message3:
    sent = False
    expected = parser.parse('February 15 2023')
    content = "NBA All-Star Weekend is coming up with the All-Star game on Feb 19, 2023!"

message_list = [message1,message2,message3]

@client.event
async def on_ready():
  print("We have logged in as {0.user}".format(client))

@client.event
async def on_message(message):

    global alert_role_made

    # Heads Up!Alerts role
    author = message.author
    if (alert_role_made == False):
        await discord.Guild.create_role(author.guild,name="Heads-Up!Alerts",color=0xf28f1d)
        alert_role_made = True
    role = discord.utils.get(author.guild.roles,name = "Heads-Up!Alerts")

    if message.author == client.user:
        return

    # Test message if bot is working
    if message.content.startswith("!ball hello"):
        role = discord.utils.get(message.author.guild.roles,name = "Heads-Up!Alerts")
        await message.channel.send(f"Hello! This bot is well and working. Try '!ball info' to see how the bot works. {role.mention}")

    # Bot introduction
    if message.content.startswith("!ball info"):
    
        embedVar = discord.Embed(title="Hello there!",color=0xf28f1d,description="Heads-Up! Basketball is a bot created by Danish Islam to keep you updated on recent events and scores in the NBA and CEBL. \n\n Read about the two main functions of the bot below:\n\n")
    
        embedVar.add_field(name = "1. Reminders About Important Season Events",value="Heads-Up! Basketball will alert you with recent news in your discord server. \n\n If you would like to be alerted type **!ball notif_on** to get a role so that you can be pinged for news or **!ball notif_off** if you would like to turn them off.",inline=False)

        embedVar.add_field(name = "2. Ask for Game Progress and League Standings",value="Chilling in a voice call when today's games cross your mind? Check the game schedule for the day, current scores and standings with our commands!\n\n For a table of commands type **!ball commands**.",inline=False)

        embedVar.set_image(url='https://media-cldnry.s-nbcnews.com/image/upload/newscms/2016_15/1494926/ss-160413-kobe-bryant-mn-13.jpg')
    
        await message.channel.send(embed=embedVar)
    
    # Command List
    if message.content.startswith("!ball commands"):

        embedVar = discord.Embed(title="Command List",color=0xf28f1d)

        embedVar.add_field(name = "Notifications",inline=False,value="**!ball notif_on**: get assigned a role so that you can be pinged for season reminders and important dates\n **!ball notif_off**: remove your role so that you don't get notifications for reminders and etc.\n")

        embedVar.add_field(name = "NBA Commands",inline=False,value = "Current State of NBA: Summer League Just Ended.\n\n **!ball NBA_today**: get a look at the game schedule for today\n **!ball NBA_east**: look at the eastern conference NBA standings\n**!ball NBA_west**: look at the western conference NBA standings\n **!ball NBA_transaction**: look at a summer of the player transactions over the past 2 days.")
                            
        embedVar.add_field(name = "CEBL Commands",value= "Current State of CEBL: Currently in the Regular Season.\n\n **!ball CEBL_today**: get a look at the game schedule for today\n **!ball CEBL_standings**: look at the CEBL standings\n",inline=False)
                       
        embedVar.add_field(name = "Feedback",inline=False, value="**!ball feedback**: report feedback or suggestions for Heads-Up Baketball!")

        embedVar.set_image(url='https://www.gannett-cdn.com/-mm-/dfff082d1e4931b30569ae37195b6862a6a8ef8a/c=0-361-2915-2008/local/-/media/2018/05/22/USATODAY/USATODAY/636625868623447717-AP-APTOPIX-Heat-Bucks-Basketball-39255807.JPG?width=2915&height=1647&fit=crop&format=pjpg&auto=webp')
    
        await message.channel.send(embed=embedVar)
    
    # Notifications on or off
    if message.content == "!ball notif_on":
        await discord.Member.add_roles(author,role)
        await message.channel.send("You've received the Heads-Up!Alerts role. :basketball:")
    
    if message.content == "!ball notif_off":
        await discord.Member.remove_roles(author,role)
        await message.channel.send("You've removed the Heads-Up!Alerts role. :basketball:")

    # Show NBA game progress that day 
    if message.content == '!ball NBA_today':
        embedVar = discord.Embed(title='CEBL Games Today',color=0xf28f1d,description='What do we got today?')
        embedVar.add_field(name = ":basketball: :books: :robot: ",value='No games today! The NBA regular season starts October 19, 2022.',inline=False)
        await message.channel.send(embed=embedVar)

    # Show NBA standings
    if message.content == '!ball NBA_east':
        NBA_east = NBA_Eastern_Standings()
        formatted = '```'+NBA_east.to_string()+'```'
        #await message.channel.send(formatted)

        embedVar = discord.Embed(title='2021-22 Eastern Conference Standings',color=0xf28f1d,description='The NBA season has ended. The next season will begin October 19, 2022.')
        embedVar.add_field(name = ":basketball: :books: :robot: ",value=formatted,inline=False)
        await message.channel.send(embed=embedVar)

    if message.content == '!ball NBA_west':
        NBA_west = NBA_Western_Standings()
        formatted = '```'+NBA_west.to_string()+'```'
        #await message.channel.send('```'+formatted+'```')

        embedVar = discord.Embed(title='2021-22 Western Conference Standings',color=0xf28f1d,description='The NBA season has ended. The next season will begin October 19, 2022.')
        embedVar.add_field(name = ":basketball: :books: :robot: ",value=formatted,inline=False)
        await message.channel.send(embed=embedVar)

    # NBA Transactions
    if message.content == '!ball NBA_transaction':

        embedVar = discord.Embed(title="Recent Player Transactions",color=0xf28f1d,description=":basketball: :books: :robot:")

        url = 'https://www.espn.com/nba/transactions'
        page = requests.get(url)
        soup = BeautifulSoup(page.text,'lxml')

        for i in range(3):
            list = []
            day = soup.find_all('div',{'class':'ResponsiveTable'})[i]
            day_date = day.find('div',{'class':'Table__Title'}).text
            table = day.find('tbody')
            for row in table.find_all('tr'):
                news = row.find_all('td')[1].text + '\n\n'
                team = row.find_all('td')[0].find('a')['href'].split('/')[-1]
                team = " ".join(team.split('-')).title()
                team = team + " " + NBA_emoji(team) + ':\n'

                list.append(team)
                list.append(news)
            embedVar.add_field(name = day_date + '\n',value="".join(list),inline=False)
        await message.channel.send(embed=embedVar)

    # Show CEBL game progress that day
    if message.content == '!ball CEBL_today':
        CEBL = CEBL_today()
        formatted = '```'+CEBL.to_string()+'```'
        #formatted = '```'+CEBL.to_markdown(tablefmt="grid")+'```'
        embedVar = discord.Embed(title='CEBL Games Today',color=0xf28f1d,description='What do we got today?')
        if CEBL.empty:
            embedVar.add_field(name = ":basketball: :books: :robot: ",value='No games today! Check back tomorrow.',inline=False)
        else:
            embedVar.add_field(name = ":basketball: :books: :robot: ",value=formatted,inline=False)
        #embedVar.add_field(name = ":basketball: :books: :robot: ",value=formatted,inline=False)
        await message.channel.send(embed=embedVar)

    # Show CEBL Standings
    if message.content == '!ball CEBL_standings':
        CEBL = CEBL_Standings()
        formatted = '```'+CEBL.to_string()+'```'
        embedVar = discord.Embed(title='2022 CEBL Season Standings',color=0xf28f1d,description='The CEBL regular season is ongoing, playoffs being August 7th!')
        embedVar.add_field(name = ":basketball: :books: :robot: ",value=formatted,inline=False)
        await message.channel.send(embed=embedVar)

    # Feedback
    if message.content == '!ball feedback':
        embedVar = discord.Embed(title='Heads-Up! Feedback',color=0xf28f1d,description='*It is a contstant quest to try to be better today than you were yesterday and better tomorrow than you were the day before.* - Kobe Bryant')
        embedVar.add_field(name = "Google Form Below",value='Link',inline=False)
        embedVar.set_image(url='https://64.media.tumblr.com/tumblr_m4l78eb4zE1ruj0bpo1_1280.jpg')
        await message.channel.send(embed=embedVar)

    # Notifications
    global message_list

    # if(valid_announcement(message1.sent,message1.expected)==True):
    #     await message.channel.send(f"{role.mention}" + message1.content)
    #     message1.sent = True

    for mess in message_list:
        if(valid_announcement(mess.sent,mess.expected)==True):
            await message.channel.send(f"{role.mention}" + mess.content)
            mess.sent = True

client.run('TOKEN')
