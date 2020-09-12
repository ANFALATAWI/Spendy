# Highest priority:
# A script that reads the data and enters it into a csv sheet
# Run with a cron job
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Data Science libraries
import pandas as pd

# Globals
charge_type = None # determined later by init_app()

# bank_func_mapping('alinmaa': alinmaa_extractor ) # TODO
quireis = {'alinmaa': 'from:alinma@alinma.com'}

def init_user():

    """
    Initialises & returns the user's crediantials object, used to access the user's mailbox.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in
    # This will open a browser window for the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def init_app():
    """
    Choose bank-specific data such as email subjects,
    Defines different dicts
    
    """
    
    if BANK_NAME.lower() == 'alinmaa':
        charge_type = {'عملية مشتريات دولية عبر نقاط البيع مدى أثير': 'pos',
            'شراء بطاقة مدى من نقطة بيع (تطبيق Apple Pay)': 'pos',
            'عملية مشتريات نقاط البيع دولية': 'pos',
            'عملية سداد الفواتير': 'bill',
            'سحب نقدي من أجهزة الصراف الآلي لبنوك أخرى': 'atm',
           }
    else:
        # Throw an exception?
        pass

def email_ids_from_query(query):
    """
    Takes a gmail query str and returns a list of emails ids list(str).
    Limit: last 100 emails
    
    """
    assert isinstance(query, str)
    
    # This results can be one or multiple messages
    # Call the Gmail API
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages') # Returns last 100
    
    if messages is not None:
        # Extract only ids from the results
        print('> Extracting messages...')
        ids = list()
        for message in messages:
            ids.append(message['id'])
    else:
        seconds = 0 # Create a config file for seconds?
        print('> No new charges have been found.')
        print('> Waiting ' + str(seconds) + ' seconds for charges...')
        # sleep for an amount of time
        # log message TODO: Google python logging
        return
        check_for_charges()
        # Exit?
    
    return ids

def snippet_from_id(ID):
    """
    Takes email ID str and returns email snippet str and info object with type
    format:
        snippet, info
    """
    results = service.users().messages().get(userId='me', id=ID).execute()
    
    info = dict()
    
    # Extract emails subject to find out which type of charge was performed
    headers = results['payload']['headers']
    subject = list(filter(lambda header: header['name'] == 'Subject', headers))
    info['type'] = get_type(subject[0]['value'])
    
    return results['snippet'], info

def extract_info(info, snippet):
    """
    This takes in a snippet of an email
    and the info object contating the type of email
    
    and extracts the rest of the info from snippet
    depending on its type
    
    """
    # Depending on sippet TYPE, extract info
    # If type = x then exttract this way & so on
    
    words = snippet.split(' ')
    
    if snippet == 'pos':
        # look for keyword
        shiraa_i = words.index('شراء')
        # use next keyword
        value_i = shiraa_i + 1
        info['Method'] # might remove
        info['Amount'] = float(words[value_i])
        info['Date']
        info['Merchant']
        info['Category'] = predict_category(info['Merchant'])
        info['type'] = type_[subject]
    
    elif snippet == 'atm':
        pass

def check_for_charges(service):
    """
    Async func
    checks for emails
    enques their ids into q
    
    """
    email_ids_from_query(quereis[BANK_NAME])
    
    # for now, I think checking for the sender (Bank) is a good idea
    # from = 'alinma@alinma.com'
    # then, filter depending on the email's subject
    
    for ID in email_ids:
        snippet, info = snippet_from_id(ID)
        info = extract_info(snippet)
        update_csv(info)

def init_csv():
    df = pd.DataFrame(columns = ['Method','Amount', 'Category', 'merchant', 'Date'])
    return df

def update_csv(info):
    
    assert ininstance(info, dict)
    temp_df = pd.DataFrame({'Amount':[info['Amount']],
                           'Category':[info['Category']],
                           'Merchant':[info['Merchant']],
                           'Method':[info['Method']],
                           'Date':[info['Date']]})
    df.append(temp_df)

    pass

def export_csv():
    """
    """
    pass

def send_to_notion():
    """
    """
    pass

def predict_category(merchant):
    """
    """
    pass

def convert_date(date_str):
    """
    Takes a date str in the format '2020-09-01'
    and returns a Date.date() object
    """
    # TODO: Decide on a format for date, date-time?
    return pd.Timestamp(date_str)

if __name__ == "__main__":
    # Consts
    SECONDS = 60

    Banks = ['Alinmaa']
    print('> The currently supported banks are: ' + ' '.join(Banks) + '.')

    BANK_NAME = input("> What's your bank's name? ").lower()

    if BANK_NAME not in Banks:
        print("> Sorry, Spendy doesn't support "+ BANK_NAME +" yet, help implement this support by contacting ...")

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    # Initialize user & extract tokens
    service = init_user()

    # Print the user's info for validation. LOG info.
    results = service.users().getProfile(userId='me').execute()
    profile_info = results.get('emailAddress')
    print("This is the email address used: " + profile_info)
    
    # Initialize an empty dataframe
    dataframe = init_csv()

    # This initializes the Bank-specific information used by the extractors
    init_app()

    # This is a blocking function, figure out how to perform it asynchronasly
    check_for_charges(service)

    # Upon a command (or a cron job), do these:
    export_csv()
    