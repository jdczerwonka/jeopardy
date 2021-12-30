#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

#%%
def map_substring(s, dict_map):
    for key in dict_map.keys():
        if key in s: return dict_map[key]
    return None

tournament_dict = {
    "Greatest of All Time" : "Greatest of All Time",
    "Teachers Tournament" : "Teachers Tournament",
    "College Championship" : "College Championship",
    "Tournament of Champions" : "Tournament of Champions",
    "Teen Tournament" : "Teen Tournamet", 
    "All-Star Games" : "All-Star Games", 
    "Power Players" :  "Power Players", 
    "Battle of the Decades" : "Battle of the Decades",
    "IBM Challenge" : "IBM Challenge", 
    "Kids Week" : "Kids Week", 
    "Celebrity" : "Celebrity Jeopardy!", 
    "Million Dollar Masters" : "Million Dollar Masters",
    "International" : "International Tournament", 
    "Teen Reunion" : "Teen Reunion Tournament",
    "Olympic" : "Olympic", 
    "Senior" : "Seniors Tournament",
    "10th Anniversary" : "10th Anniversary Tournament",
    "Super Jeopardy!" : "Super Jeopardy!"
}

week_dict = {
    "Back to School": "Back to School Week", 
    "Armed Forces" : "Armed Forces Week",
    "Boston Week" : "Boston Week"
}

tournament_bracket_dict = {
    ' final ' : 'final',
    'quarterfinal' : 'quarterfinal', 
    'semifinal' : 'semifinal'
}

#%%
episode_list = []

seasons_url = 'http://www.j-archive.com/listseasons.php'
html_text = requests.get(seasons_url).text
soup = BeautifulSoup(html_text, 'html.parser')

for tr_season in soup.find('table').find_all('tr'):
    season_url = tr_season.find('a').get('href')
    season = tr_season.find('a').text

    html_text = requests.get('http://j-archive.com/' + season_url).text
    soup_season = BeautifulSoup(html_text, 'html.parser')

    print(season)
    for tr in soup_season.find('table').find_all('tr'):
        show = tr.find('a')
        episode_list.append([
            season,
            show.get('href').split('?game_id=')[1],
            show.text.split(',')[0],
            show.text[-10:],
            tr.find_all('td')[2].text
        ])

df = pd.DataFrame(episode_list, columns=['Season', 'J Archive ID', 'Episode Number', 'Airdate', 'Comment'])
df['Comment'] = df['Comment'].str.strip()

df['Tournament'] = df['Comment'].apply(lambda x: map_substring(x, tournament_dict))
df['Week'] = df['Comment'].apply(lambda x: map_substring(x, week_dict))
df['Tournament Level'] = df['Comment'].apply(lambda x: map_substring(x, tournament_bracket_dict))
save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/jeopardy_episodes.csv'
df.to_csv(save_path, index=False)


# %%
df_episodes = pd.read_csv(os.path.expanduser('~') + '/Desktop/Jeopardy/jeopardy_episodes.csv')
seasons_exclude = ['Season 37', 'Season 36']
seasons = df_episodes['Season'].drop_duplicates().tolist()
seasons = list(set(seasons) - set(seasons_exclude))

for season in seasons:
    print(season)
    episodes = df_episodes[df_episodes['Season'].isin([season])]['J Archive ID'].tolist()

    contestant_game_list = []

    for episode in episodes:
        html_text = requests.get('http://www.j-archive.com/showgame.php?game_id=' + str(episode)).text
        soup = BeautifulSoup(html_text, 'html.parser')
        contestants = soup.find_all(class_='contestants')

        position = 1
        for contestant in soup.find_all(class_='contestants'):
            contestant_game_list.append([
                episode,
                contestant.find('a').get('href').split('?player_id=')[1],
                position
            ])
            position = position + 1

    df = pd.DataFrame(contestant_game_list, columns=['J Archive Game ID', 'J Archive Contestant ID', 'player position'])
    
    if season == 'Jeopardy!: The Greatest of All Time':
        season = 'goat'
    elif season == 'Super Jeopardy!':
        season = 'super'

    save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/Episode Contestants/jeopardy_episode_contestants_' + season + '.csv'
    df.to_csv(save_path, index=False)

df_list = []
for file in os.listdir(os.path.expanduser('~') + '/Desktop/Jeopardy/Episode Contestants'):
    df_list.append(pd.read_csv(os.path.expanduser('~') + '/Desktop/Jeopardy/Episode Contestants/' + file))

save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/jeopardy_episode_contestants.csv'
pd.concat(df_list, ignore_index=True).to_csv(save_path, index=False)

# %%
episode_contestant_df = pd.read_csv(os.path.expanduser('~') + '/Desktop/Jeopardy/jeopardy_episode_contestants.csv')
episode_df = pd.read_csv(os.path.expanduser('~') + '/Desktop/Jeopardy/jeopardy_episodes.csv')
merged_df = episode_contestant_df.merge(episode_df[['J Archive ID', 'Airdate']], how='left', left_on='J Archive Game ID', right_on='J Archive ID')
merged_df = merged_df[['J Archive Contestant ID', 'Airdate']].groupby(by='J Archive Contestant ID', as_index=False).min().sort_values('Airdate', ascending=False)
merged_df['Year'] = pd.to_datetime(merged_df['Airdate']).dt.year
merged_df['Year Factor'] = ((merged_df['Year'] - 1980) / 5).round(0)

factor_list = merged_df['Year Factor'].drop_duplicates().tolist()
factor_list = [0]
for year_factor in factor_list:

    print(year_factor)
    contestant_id_list = merged_df[merged_df['Year Factor'].isin([year_factor])]['J Archive Contestant ID'].tolist()
    # contestant_id_list = merged_df[merged_df['Year'].isin(['2021'])]['J Archive Contestant ID'].tolist()
    contestant_list = []

    for contestant_id in contestant_id_list:
        print(contestant_id)
        html_text = requests.get('http://www.j-archive.com/showplayer.php?player_id=' + str(contestant_id)).text
        soup = BeautifulSoup(html_text, 'html.parser')
        occupation_origin = soup.find(class_='player_occupation_and_origin').text

        #A Washington, D.C. anchor from BBC World News America...
        #A TV, film and Broadway actress from Malcolm in the Middle and Raising the Bar...
        #A Grammy winner, Oscar nominee and multi-talented performer from Hairspray and The Pajama Game...
        #An actor, comedian and singer from The Wayne Brady Show...
        #An actress, director and producer from The Silence of the Lambs..
        #An attorney, correspondent and co-host from The View...
        #A television's favorite psychiatrist, Dr. Frasier Crane from Frasier...
        #A star of the world's favorite game show, from Wheel of Fortune...
        if (contestant_id == 7819 or contestant_id == 6502 or contestant_id == 6417 or 
            contestant_id == 6219 or contestant_id == 6129 or contestant_id == 6099 or
            contestant_id == 8486 or contestant_id == 7938):
            occupation_origin = occupation_origin.replace(',', '')
        #An actress from Kate & Allie and 3rd Rock from the Sun...
        #An actress from 3rd Rock from the Sun...
        #An actor from 3rd Rock from the Sun...
        elif contestant_id == 6795 or contestant_id == 2446 or contestant_id == 6064:
            occupation_origin = occupation_origin.replace('3rd Rock from the Sun', '3rd Rock frm the Sun')
        #A columnist and author from Greetings from the Lincoln Bedroom...
        elif contestant_id == 5102:
            occupation_origin = occupation_origin.replace('from the Lincoln Bedroom', 'frm the Lincoln Bedroom')

        if occupation_origin.count('from') == 1:
            if occupation_origin.count(',') == 1:
                city = occupation_origin.split('from ')[1].split(',')[0]
                state = occupation_origin.split('from ')[1].split(',')[1].replace('...', '')
                college = None
                company = None
            elif occupation_origin.count(',') == 0:
                city = None
                state = None
                college = None
                company = occupation_origin.split('from ')[1].split(',')[0].replace('...', '')
        elif occupation_origin.count('from') == 2:
            city = occupation_origin.split('from ')[2].split(',')[0]
            state = occupation_origin.split('from ')[2].split(',')[1].replace('...', '')
            college = occupation_origin.split('from ')[1].strip()
            company = None
        
        if occupation_origin.split('from ')[0] == '':
            occupation = None
        else:
            occupation = occupation_origin.split('from ')[0].split(' ', 1)[1].replace(' originally', '').strip()

        contestant_list.append([
            contestant_id,
            occupation,
            occupation_origin.split('from ')[0].count('originally')>0,
            city,
            state,
            college,
            company
        ])
    
    save_str = str(1980 + (year_factor*5)) + '_' + str(1980 + ((year_factor+1)*5) - 1)
    save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/Contestants/jeopardy_contestants_' + save_str + '.csv'
    pd.DataFrame(contestant_list, columns=['J Archive Contestant ID', 'Occupation', 'Originally', 'City', 'State', 'College', 'Company']).to_csv(save_path, index=False)

df_list = []
for file in os.listdir(os.path.expanduser('~') + '/Desktop/Jeopardy/Contestants'):
    df_list.append(pd.read_csv(os.path.expanduser('~') + '/Desktop/Jeopardy/Contestants/' + file))

save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/jeopardy_contestants.csv'
pd.concat(df_list, ignore_index=True).to_csv(save_path, index=False)

#%%
episode_df = pd.read_csv(os.path.expanduser('~') + '/Desktop/Jeopardy/jeopardy_episodes.csv')
seasons_list = episode_df['Season'].drop_duplicates().tolist()
del seasons_list[:8]
# seasons_list = ['Season 35']

for season in seasons_list:
    print(season)
    episode_list = episode_df[episode_df['Season'].isin([season])]['J Archive ID'].tolist()
    # episode_list = [6227]

    category_list = []
    clue_list = []

    for episode_id in episode_list:
        print(episode_id)
        html_text = requests.get('http://www.j-archive.com/showgame.php?game_id=' + str(episode_id)).text
        soup = BeautifulSoup(html_text, 'html.parser')

        if soup.find(id='jeopardy_round') != None:
            category_count = 1
            for category_name in soup.find(id='jeopardy_round').find_all(class_="category_name"):
                category_list.append([
                    episode_id,
                    'R1',
                    category_name.text,
                    category_count
                ])
                category_count = category_count + 1

        if soup.find(id='double_jeopardy_round') != None:
            category_count = 1
            for category_name in soup.find(id='double_jeopardy_round').find_all(class_="category_name"):
                category_list.append([
                    episode_id,
                    'R2',
                    category_name.text,
                    category_count
                ])
                category_count = category_count + 1
        
        if soup.find_all(class_='final_round') != None:
            final_count = 1
            for category_name in soup.find_all(class_='final_round'):
                category_list.append([
                    episode_id,
                    'F' + str(final_count),
                    category_name.find(class_="category_name").text,
                    final_count
                ])
                final_count = final_count + 1

        if soup.find(id='jeopardy_round') != None:
            clue_count = 1
            for clue in soup.find(id='jeopardy_round').find_all(class_="clue"):
                if clue.find(class_='clue_text') == None:
                    clue_text = None
                    daily_double = None
                    clue_value = None
                    clue_value_dd = None
                    clue_order = None
                    clue_position = None
                    clue_answer = None
                else:
                    if clue.find(class_='clue_value') == None:
                        daily_double = True
                        clue_value = None
                        clue_value_dd = clue.find(class_='clue_value_daily_double').text[4:].replace('$', '').replace(',', '')
                    else:
                        daily_double = False
                        clue_value = clue.find(class_='clue_value').text.replace('$', '')
                        clue_value_dd = None
                    clue_text = clue.find(class_='clue_text').text
                    clue_order = clue.find(class_='clue_order_number').text
                    clue_position = clue.find('div')['onmouseover'].split(',')[0][8:-1]
                    clue_answer = clue.find('div')['onmouseover'].split('</em>')[0].split('<em class="correct_response">')[1].replace('<i>', '').replace('</i>', '')

                clue_list.append([
                    episode_id,
                    'R1',
                    clue_text,
                    clue_answer,
                    clue_value,
                    clue_value_dd,
                    daily_double,
                    clue_order,
                    clue_position,
                    'R1_' + str(int((clue_count - 1) / 6)+1) + '_' + str(((clue_count - 1) % 6)+1)
                ])
                clue_count = clue_count + 1

        if soup.find(id='double_jeopardy_round') != None:
            clue_count = 1
            for clue in soup.find(id='double_jeopardy_round').find_all(class_="clue"):
                if clue.find(class_='clue_text') == None:
                    clue_text = None
                    daily_double = None
                    clue_value = None
                    clue_value_dd = None
                    clue_order = None
                    clue_position = None
                    clue_answer = None
                else:
                    if clue.find(class_='clue_value') == None:
                        daily_double = True
                        clue_value = None
                        clue_value_dd = clue.find(class_='clue_value_daily_double').text[4:].replace('$', '').replace(',', '')
                    else:
                        daily_double = False
                        clue_value = clue.find(class_='clue_value').text.replace('$', '')
                        clue_value_dd = None
                    clue_text = clue.find(class_='clue_text').text
                    clue_order = clue.find(class_='clue_order_number').text
                    clue_position = clue.find('div')['onmouseover'].split(',')[0][8:-1]
                    clue_answer = clue.find('div')['onmouseover'].split('</em>')[0].split('<em class="correct_response">')[1].replace('<i>', '').replace('</i>', '')

                clue_list.append([
                    episode_id,
                    'R2',
                    clue_text,
                    clue_answer,
                    clue_value,
                    clue_value_dd,
                    daily_double,
                    clue_order,
                    clue_position,
                    'R2_' + str(int((clue_count - 1) / 6)+1) + '_' + str(((clue_count - 1) % 6)+1)
                ])
                clue_count = clue_count + 1
        
        if soup.find_all(class_='final_round') != None:
            clue_count = 1
            for clue in soup.find_all(class_='final_round'):
                clue_list.append([
                    episode_id,
                    'F' + str(clue_count),
                    clue.find(class_='clue_text').text,
                    clue.find('div')['onmouseover'].split('</em>')[0].split('correct_response')[1][3:].replace('<i>', '').replace('</i>', ''),
                    None,
                    None,
                    False,
                    clue_count,
                    clue.find('div')['onmouseover'].split(',')[0][8:-1],
                    'F' + str(clue_count)
                ])
                clue_count = clue_count + 1
    
    clue_df = pd.DataFrame(clue_list, columns=['J Archive Game ID', 'Round', 'Clue', 'Answer', 'Clue Value',
        'Daily Double Value', 'Is Daily Double', 'Order', 'Clue Position 1', 'Clue Position 2'])
    category_df = pd.DataFrame(category_list, columns=['J Archive Game ID', 'Round', 'Category', 'Category Position'])

    if season == 'Jeopardy!: The Greatest of All Time':
        season = 'goat'
    elif season == 'Super Jeopardy!':
        season = 'super'

    save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/Categories/jeopardy_categories_' + season + '.csv'
    category_df.to_csv(save_path, index=False)

    save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/Clues/jeopardy_clues_' + season + '.csv'
    clue_df.to_csv(save_path, index=False)

# %%
episode_df = pd.read_csv(os.path.expanduser('~') + '/Desktop/Jeopardy/jeopardy_episodes.csv')
seasons_list = episode_df['Season'].drop_duplicates().tolist()
seasons_list = ['Season 36']

for season in seasons_list:
    print(season)
    episode_list = episode_df[episode_df['Season'].isin([season])]['J Archive ID'].tolist()
    # episode_list = [6916]

    balance_list = []
    results_list = []

    for episode_id in episode_list:
        print(episode_id)
        html_text = requests.get('http://www.j-archive.com/showscores.php?game_id=' + str(episode_id)).text
        soup = BeautifulSoup(html_text, 'html.parser')

        for x in range(len(soup.find(id='jeopardy_round').find_all('tr'))):
            clue = soup.find(id='jeopardy_round').find_all('tr')[x]
            if x != 0:
                for y in range(5):
                    td = clue.find_all('td')[y]
                    if not(y == 0 or y == 4):
                        balance_list.append([
                            episode_id,
                            'R1',
                            x,
                            4 - y,
                            td.text.replace('$', '').replace(',', '')
                        ])

        for x in range(len(soup.find(id='double_jeopardy_round').find_all('tr'))-1):
            clue = soup.find(id='double_jeopardy_round').find_all('tr')[x]
            if x != 0:
                for y in range(5):
                    td = clue.find_all('td')[y]
                    if not(y == 0 or y == 4):
                        balance_list.append([
                            episode_id,
                            'R2',
                            x,
                            4 - y,
                            td.text.replace('$', '').replace(',', '')
                        ])

        scores = soup.find(id='final_jeopardy_round').find('table').find_all('tr')
        remarks = soup.find(id='final_jeopardy_round').find_all(class_='score_remarks')
        has_tie_break = len(soup.find(id='final_jeopardy_round').find_all('h2')) > 1
        for x in range(3):
            score = scores[1].find_all('td')[x].text.replace('$', '').replace(',', '')

            balance_list.append([
                episode_id,
                'F1',
                1,
                3 - x,
                score
            ])

            if has_tie_break:
                balance_list.append([
                    episode_id,
                    'F2',
                    1,
                    3 - x,
                    score
                ])                

            if remarks[0].text != '':
                if remarks[x].text.count('champion') > 0:
                    if remarks[x].text.count('Tournament champion') > 0:
                        score = remarks[x].text.split(':')[1].replace('$', '').replace(',', '')
                else:
                    if remarks[x].text.count(':') > 0:
                        score = remarks[x].text.split(':')[1].replace('$', '').replace(',', '')
                    else:
                        score = remarks[x].text
            else:
                score = 0

            results_list.append([
                episode_id,
                3 - x,
                score
            ])

    balance_df = pd.DataFrame(balance_list, columns=['J Archive Game ID', 'Round', 'Clue', 'Position', 'Balance'])
    results_df = pd.DataFrame(results_list, columns=['J Archive Game ID', 'Position', 'Score'])

    if season == 'Jeopardy!: The Greatest of All Time':
        season = 'goat'
    elif season == 'Super Jeopardy!':
        season = 'super'

    save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/Balances/jeopardy_balances_' + season + '.csv'
    balance_df.to_csv(save_path, index=False)
    save_path = os.path.expanduser('~') + '/Desktop/Jeopardy/Results/jeopardy_results_' + season + '.csv'
    results_df.to_csv(save_path, index=False)


# %%
html_text = requests.get('http://www.j-archive.com/showscores.php?game_id=6917').text
soup = BeautifulSoup(html_text, 'html.parser')
print(soup.find(id='final_jeopardy_round').find('table').find_all('tr'))

# %%
print(remarks[x])
# print(x)
# %%
