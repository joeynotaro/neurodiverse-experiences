# in the terminal use python3 command, not python
# type 'pyhon3 {file_path}'

# import libaries
import pandas as pd
import requests
import os
import datetime


# function to gather user input
def gather_user_input():
    # asks the user to provide two subreddits of interest and authorization credentials
    subred_1 = input('What is the first subreddit from which you would like to collect data? ')
    subred_2 = input('What is the second subreddit from which you would like to collect? ')
    client_id = input('What is your API client ID? ')
    client_secret =  input('What is your API client secret? ')
    user_agent =  input('What is the user agent? ')
    username =  input('What is the user name? ')
    password =  input('What is the password? ')
    
    # stores all user data solicited above into a dictionary
    user_info = [{
    'subred_1': subred_1,
    'subred_2': subred_2,
    'client_id': client_id,
    'client_secret': client_secret,
    'user_agent': user_agent,
    'username': username,
    'password': password
    }]
    
    # stores the user data dictionary into a a json file to be read later
    pd.DataFrame(user_info).to_json('./data_files/user_info.json')
    
    # prints a message to the user indicating credentials stored or throws error if failed
    try:
        if os.path.exists('./data_files/user_info.json'):
            print("User credentials successfully stored.")
    except Exception as E:
        print(f'Error is {E}.')
        

# function to authorize user credentials
def authorize_creds():
    # reads in json file with stored user credential data
    user_info = pd.read_json('./data_files/user_info.json')
    
    # uses user credentials to define authorization and data access
    auth = requests.auth.HTTPBasicAuth(user_info.loc[0, 'client_id'], user_info.loc[0, 'client_secret'])
    data = {
        'grant_type': 'password',
        'username': user_info.loc[0, 'username'],
        'password': user_info.loc[0, 'password']
    }
    #create an informative header for your application
    headers = {'User-Agent': 'joey/0.0.1'}
    
    # submits request to API
    res = requests.post(
        'https://www.reddit.com/api/v1/access_token',
        auth=auth,
        data=data,
        headers=headers)
    
    # prints response code to user, 200 if status ok
    print(res)
    
    #retrieve access token
    token = res.json()['access_token']

    # creates access token in headers for scraping data
    headers['Authorization'] = f'bearer {token}'
    
    # submits request to API
    requests.get('https://oauth.reddit.com/api/v1/me', headers=headers).status_code == 200
    
    # returns new header with access token for use in webscraper
    return headers



# function to webscrape Reddit API
def api_scrape(headers):
    # reads in the user credentials to pull the two subreddits of interest
    user_info = pd.read_json('./data_files/user_info.json')
    base_url = 'https://oauth.reddit.com/r/'
    subreddits = [user_info.loc[0, 'subred_1'], user_info.loc[0, 'subred_2']]
    
    # create an empty list to append a text dictionary of one post at a time
    posts = []
    
    # creates a for loop to iterate through both of the subreddits of interest
    for subreddit in subreddits:
        
        # creates a for loop to collect up to 100 posts at a time 10 separate times
        for i in range(10):
            # sets post collection limit to 100 per API restrictions
            if i == 0:
                params = {
                    'limit': 100
                }
            # pagination set after first iteration to gather next 100 posts
            else:
                params = {
                    'after': after_param,
                    'limit': 100
                }
            
            # submits request to API and stores in res variable
            res = requests.get(base_url+subreddit, 
                               headers=headers, 
                               params = params)
            
            # loops through all the subreddit posts in the get request, up to 100
            for j in range(len(res.json()['data']['children'])):
                # creates an empty dictionary each post and stores title, selftext, and subreddit
                text = {}
                text['title'] = res.json()['data']['children'][j]['data']['title']
                text['selftext'] = res.json()['data']['children'][j]['data']['selftext']
                text['subreddit'] = res.json()['data']['children'][j]['data']['subreddit']
                # appends the whole text dictionary to the post list if it is not a duplicate title
                if text['title'] not in posts:
                    posts.append(text)
            
            # sets the after parameter for next 100 posts if it exists; otherwise ends for loop
            try:
                after_param = res.json()['data']['children'][-1]['data']['name']
            except:
                pass
    
    # checks if csv file storing all posts already exists
    # if csv file does exist, reads in the file, creates a df of the posts just created,
    # concatenates the two dfs, stores as csv file, and then accesses transaction log
    if os.path.exists('./data_files/subreddit_posts.csv'):
        subreddit_posts = pd.read_csv('./data_files/subreddit_posts.csv')
        new_posts = pd.DataFrame(posts)
        subreddit_posts = pd.concat([subreddit_posts, new_posts], ignore_index = True)
        subreddit_posts.to_csv('./data_files/subreddit_posts.csv', index = False)
        transaction_log(posts, subreddit_posts)
    # if csv file does not exist, creates a df of the posts just created, stores as csv file,
    # then accesses transaction log
    else:
        subreddit_posts = pd.DataFrame(posts)
        subreddit_posts.to_csv('./data_files/subreddit_posts.csv', index = False)
        transaction_log(posts, subreddit_posts)
    
    # returns the df for user to see
    return subreddit_posts
    
    

# function to create and update transaction log
def transaction_log(posts, subreddit_posts):
    # creates an empty list to store new log entry as a dictionary
    new_log = []
    
    # if transaction log already exists, reads in the log,
    # creates a new log entry as a list with a dictionary, 
    # saves new log entry as a df, concatenates both logs,
    # then saves transaction log as csv
    if os.path.exists('./data_files/transaction_log.csv'):
        trans_log = pd.read_csv('./data_files/transaction_log.csv')
        current_log = [{'datetime_retrieved': datetime.datetime.now(), 
                       'posts_retrieved': len(posts), 
                       'total_posts': subreddit_posts.shape[0]}]
        new_log = pd.DataFrame(current_log)
        trans_log = pd.concat([trans_log, new_log], ignore_index = True)
        trans_log.to_csv('./data_files/transaction_log.csv', index = False)
    # If not transaction log exists yet, 
    # creates a new log entry as a list with a dictionary,
    #saves new log entry as a df, then saves transaction log as csv
    else:
        current_log = [{'datetime_retrieved': datetime.datetime.now(), 
                       'posts_retrieved': len(posts), 
                       'total_posts': subreddit_posts.shape[0]}]
        trans_log = pd.DataFrame(current_log)
        trans_log.to_csv('./data_files/transaction_log.csv', index = False)
    
    # prints out transaction log status to user
    return print(f'There were {len(posts)} retrieved at {datetime.datetime.now()} for a total of {subreddit_posts.shape[0]} to date.')


# main function to execute webscraper
# if the user info json file exists, authorize credentials
if os.path.exists('./data_files/user_info.json'):
    headers = authorize_creds()
# if the user info json file does not exists, gather user input,
# then authorize credentials
else:
    gather_user_input()
    headers = authorize_creds()

# call webscrape function to run script and return response status and log status
subreddit_posts = api_scrape(headers)

# print new df shape
print(subreddit_posts.shape)

# print new df head
print(subreddit_posts.head())