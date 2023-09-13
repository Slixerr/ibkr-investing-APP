from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
import os
import time
import pandas as pd
import glob



options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--start-maximized")
options.add_argument("--window-size=1920,1080")
options.add_argument('--disable-notifications')
options.page_load_strategy = 'eager'
options.add_experimental_option("excludeSwitches", ["enable-logging"])
#options.add_argument("--user-data-dir=C:\\Users\\silvi\\AppData\\Local\\Google\\Chrome\\User Data")
driver = webdriver.Chrome(options=options)
df_cartera2_transactions = pd.DataFrame()
df_cartera3_transactions = pd.DataFrame()

def create_portfolio(name):
    #Scroll to top
    driver.execute_script("window.scrollTo(0, 220)")

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'plusTab.reverseToolTip.genToolTip.oneliner'))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="addPortfolioPopup"]/div[2]/div[2]/i'))).click()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="newPortfolioText"]'))).send_keys(name)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="createPortfolio"]'))).click()
    time.sleep(1)

def change_portfolio_tab(portfolio_name):
    input_el = driver.find_element(By.XPATH,'//*[@title="' + portfolio_name + '"]')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_el)
    input_el.click()
    time.sleep(5) #wait the table to load completly

def delete_portfolio(portfolio_name):
    change_portfolio_tab(portfolio_name)
    driver.find_element(By.CLASS_NAME, "threeDotsIcon").click()
    driver.find_element(By.CLASS_NAME, "js-delete-portfolio-button").click()
    time.sleep(1)
    elements = driver.find_elements(By.CLASS_NAME, "genPopup.noFooter") 
    for element in elements:
        if "displayNone" not in element.get_attribute('class'):
            element.find_element(By.XPATH, ".//a[contains(@onclick, 'Portfolio.deletePortfolio')]").click()
    time.sleep(5)

def get_position_quantity(symbol, type=None):

    investing_cartera = pd.read_html(driver.page_source)[0]
    investing_cartera.set_index(investing_cartera.iloc[:,2], inplace=True)
    investing_cartera = investing_cartera.iloc[:, 4:6]

    try:
        if type != None:
            quantity =  investing_cartera.loc[(investing_cartera.index == symbol) & (investing_cartera["Type"] == type), "Amount"].values[0]
        else:
            quantity =  investing_cartera.loc[(investing_cartera.index == symbol), "Amount"].values[0]
    except (IndexError, KeyError):
        quantity = 0 
    return int(quantity)



def get_transactions():
    for file in glob.glob("Datos/Transactions*.csv"):
        transactions = pd.read_csv(file)
        transactions.set_index("Id", inplace=True)
        transactions["Quantity"] = transactions['Quantity'].astype(int)
        transactions["Time"] =  pd.to_datetime(transactions["Time"], format="%Y-%m-%d  %H:%M:%S")
        return transactions


def add_position(index, symbol, isin, type, quantity, price, date, investing_sell_quantity = 0):
    global df_cartera3_transactions

    #Check if there is a same position but sell type
    sell_quantity = investing_sell_quantity

    if(sell_quantity != 0 and type == 'BUY'):
        if(sell_quantity > quantity):
            close_transaction(index, symbol, isin, "SELL", quantity, price, date)
            quantity = 0
        else:
            close_transaction(index, symbol, isin, "SELL", sell_quantity, price, date)
            quantity -= sell_quantity
    
    if quantity > 0:
        success = False
        while(success == False):
            try:
                #Scroll to top
                driver.execute_script("window.scrollTo(0, 220)")
                #Clear textbox
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[starts-with(@id,"searchText_addPos_")]'))).clear()
                #Add new position
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[starts-with(@id,"searchText_addPos_")]'))).send_keys(isin)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[starts-with(@id,"searchText_addPos_")]'))).click()
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="searchRowIdtop_0"]'))).click()
                #Date
                datepicker = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[starts-with(@id,"widgetFieldDateRange")]')))
                driver.execute_script("arguments[0].innerText = '" + date + "'", datepicker)
                #Quantity
                #print("Quedan por comprar: " + str(quantity))
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[starts-with(@id,"a_amount_")]'))).send_keys(str(quantity))
                #Set price
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[starts-with(@id,"a_price_")]'))).clear()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[starts-with(@id,"a_price_")]'))).send_keys(str(price))
                #print("compra realizada")
                success = True

            except:
                driver.refresh()
                time.sleep(5)
                #print("intento 2 compra")

        #Select type if not BUY
        if type == "SELL":
            
            select = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[starts-with(@id,"a_operation_")]'))))
            select.select_by_visible_text('SELL')

            #Cartera3-Corto 
            new_row = pd.DataFrame({"Symbol": symbol, "ISIN": isin, "Action": "SLD" , "Quantity": quantity, "Price": price , "Time": date}, index=[0])
            df_cartera3_transactions = pd.concat([df_cartera3_transactions, new_row], ignore_index=True)
            reduce_quantity_transaction(index, quantity)

        #Confirm
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[starts-with(@id,"addPositionBtn_")]'))).click()
        time.sleep(6)

def close_position(quantity, price, date):
    input_el = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-close-position')))[-1]
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_el)
    #Close position
    input_el = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-close-position')))[-1]
    input_el.click()
    #Date
    datepicker = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[starts-with(@id,"pickerrow_symbol_")]')))[-1]
    driver.execute_script("arguments[0].value = '" + date + "'", datepicker)

    if quantity > 0: #Close a quantity of shares of the position. If not, close whole position
        #Change quantity
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[starts-with(@id,"amountrow_symbol_")]')))[-1].clear()
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[starts-with(@id,"amountrow_symbol_")]')))[-1].send_keys(str(quantity))

    #Price
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[starts-with(@id,"curPricerow_symbol_")]')))[-1].clear()
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[starts-with(@id,"curPricerow_symbol_")]')))[-1].send_keys(str(price))
    #Save changes
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[starts-with(@id,"closeBtnrow_symbol_")]')))[-1].click()
    time.sleep(6.5)

def manage_container_father(symbol, action):

    input_el = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//td[@data-column-name="sum_pos_fpb_symbols" and descendant::text()="'+symbol+'"]')))
    father_class = input_el.find_element(By.XPATH, '..').get_attribute('class')
    if not (action == "CONTRACT" and  "openedParentTR" not in father_class):
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_el)
        input_el.click()
        time.sleep(1)



def close_transaction(index, symbol, isin, type, quantity, price, date):
    global df_cartera3_transactions
    positions_to_close = quantity


    investing_quantity = get_position_quantity(symbol)
    manage_container_father(symbol, "EXPAND")
    

    if (type == "SELL"): 
        #Cartera3-Corto
        new_row = pd.DataFrame({"Symbol": symbol, "ISIN": isin,  "Action": "BOT" , "Quantity": quantity, "Price": price , "Time": date}, index=[0])
        df_cartera3_transactions = pd.concat([df_cartera3_transactions, new_row], ignore_index=True)
        reduce_quantity_transaction(index, quantity)

    while (positions_to_close > 0):
        positions_rowx = int(driver.find_elements(By.XPATH, '//*[starts-with(@id,"amountrow_symbol_")]')[-1].get_attribute('value'))

        if positions_rowx > positions_to_close:
            close_position(positions_to_close, price, date)
            positions_to_close = 0

        elif positions_rowx <= positions_to_close:
            close_position(0, price, date)
            positions_to_close = positions_to_close - positions_rowx

    #print(" Resta " + type  + " investing_quantity - quantity ==" + str(investing_quantity - quantity))
    if (investing_quantity - quantity > 0):
        manage_container_father(symbol, "CONTRACT")

def reduce_quantity_transaction(index, quantity): #Cartera2-Largo
    global df_cartera2_transactions
    #try:
    old_quantity = df_cartera2_transactions.loc[index, "Quantity"]
    new_quantity = old_quantity - quantity
    if new_quantity == 0:
        df_cartera2_transactions.drop(index, inplace=True)
    else:
        df_cartera2_transactions.loc[index, "Quantity"] = new_quantity

    #print(df_cartera2_transactions)
    #except:
    #    pass

def process_portfolio(portfolio_name, transactions):
    print("Processing portfolio: " + portfolio_name)

    change_portfolio_tab(portfolio_name)

    if transactions.empty:
        return

    for i in transactions.index:
        index = i
        symbol = transactions.loc[i,"Symbol"]
        isin = transactions.loc[i,"ISIN"]
        quantity = transactions.loc[i,"Quantity"]
        price = transactions.loc[i,"Price"]
        date = transactions.loc[i, "Time"].strftime("%m/%d/%Y")
        action = transactions.loc[i,"Action"]
        investing_buy_quantity = get_position_quantity(symbol, "BUY")

        investing_sell_quantity = get_position_quantity(symbol, "SELL")


        #print(symbol + " " + action + " " + str(quantity) + " " + str(price) + " " + date)
        #print("Buy:"+ str(investing_buy_quantity))
        #print("Sell:"+ str(investing_sell_quantity))


        if(action == "BOT"):
            
            if portfolio_name == "Cartera1":
                #print(1)
                add_position(index, symbol, isin, "BUY", quantity, price, date, investing_sell_quantity)

            elif portfolio_name == "Cartera2-Largo":
                if(investing_buy_quantity != 0):
                    if (quantity > investing_buy_quantity):
                        #print(2.1)
                        close_transaction(index, symbol, isin, "BUY", investing_buy_quantity, price, date)
                    else:
                        #print(2.2)
                        close_transaction(index, symbol, isin, "BUY", quantity, price, date)

            else: #Cartera3-Corto
                if(investing_buy_quantity != 0):
                    #print(3)
                    close_transaction(index, symbol, isin, "BUY", quantity, price, date)

        #If the transaction is "sold"...
        else:
            if portfolio_name == "Cartera1":
                if quantity <= investing_buy_quantity:
                    #print(4.1)
                    close_transaction(index, symbol, isin, "BUY", quantity, price, date)
                else:
                    #print(4.2)
                    if investing_buy_quantity != 0: 
                        close_transaction(index, symbol, isin, "BUY", investing_buy_quantity, price, date)
                    remaining_quantity = quantity - investing_buy_quantity
                    add_position(index, symbol, isin, "SELL", remaining_quantity, price, date)

            elif portfolio_name == "Cartera2-Largo":  
                #print(5)
                add_position(index, symbol, isin, "BUY", quantity, price, date)
            
            #Cartera3-Corto
            else:
                #print(6)
                add_position(index, symbol, isin, "BUY", quantity, price, date)

    

        



def portfolio_initiation(): # pragma: no cover
    print("Starting new investing portfolio")
    #Read portfolio data
    df_portfolio = pd.read_csv("Datos/portfolio.csv")
    df_portfolio_investing = df_portfolio[['ISIN', 'SecType','Quantity', 'AverageCost']]
    df_portfolio_investing = df_portfolio_investing.to_csv("Datos/portfolioCSV_investing.csv", index=False)

    #New portfolio button
    driver.find_element(By.XPATH, '//*[@id="fullColumn"]/div[1]/a').click()

    #Change the hidden upload structure visibility and display as it is unaccessible to selenium
    driver.execute_script('document.getElementById("uploadFile_newportfolio").style.visibility="visible";')
    driver.execute_script('document.getElementById("uploadFile_newportfolio").style.display="block";')

    #Upload the file
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="uploadFile_newportfolio"]'))).send_keys(os.path.join(os.getcwd(), "Datos/portfolioCSV_investing.csv"))
    
    #Type of portfolio
    driver.find_element(By.XPATH, '//*[@id="importToPositions"]').click()

    #Name of the portfolio
    driver.find_element(By.XPATH, '//*[@id="importTarget"]').send_keys('Cartera1')

    #Wait in order to upload the file in time.
    time.sleep(3)

    #Next button
    driver.find_element(By.XPATH, '//*[@id="importNextBtn"]').click()
    #Next button
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="step2NextBtn"]'))).click()
    time.sleep(3)

    #Confirm portfolio
    input_el = driver.find_element(By.CLASS_NAME, 'newBtn.LightGray.Arrow.float_lang_base_2')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_el)
    input_el.click()
    driver.find_element(By.ID, 'yesBtn').click()


    #Create missing portfolios
    create_portfolio('Cartera2-Largo')
    create_portfolio('Cartera3-Corto')

    #Delete temporary file
    os.remove("Datos/portfolioCSV_investing.csv")




def main_investing(): # pragma: no cover
    global df_cartera2_transactions

    #driver.maximize_window()
    driver.get("https://www.investing.com/")
    time.sleep(5)

    #Cookies accept
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()

    #Popup appears
    try:
        driver.find_element(By.CLASS_NAME, 'popupCloseIcon.largeBannerCloser').click()
    except ElementNotInteractableException:
        pass

        
    #Log In Screen
    driver.find_element(By.XPATH, '//*[@id="userAccount"]/div/a[1]').click()

    #Account data
    with open("userCredentials.txt", 'r') as file:
        for line in file:
            if 'userInvesting' in line:
                userInvesting = line.strip().split('=')[1].strip()
            elif 'passInvesting' in line:
                passInvesting = line.strip().split('=')[1].strip()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginFormUser_email"]'))).send_keys(userInvesting)
    driver.find_element(By.XPATH, '//*[@id="loginForm_password"]').send_keys(passInvesting)

    #Log in button
    driver.find_element(By.XPATH, '//*[@id="signup"]/a').click()
    time.sleep(6)
    #My portfolio button
    #WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="navMenu"]/ul/li[2]/a'))).click()
    driver.get("https://www.investing.com/portfolio")


    transactions = get_transactions()
    df_cartera2_transactions = transactions


    #Wait page to load
    time.sleep(3)


    #Get time from last completed execution of the programm
    try:
        registry = pd.read_csv("Datos/registry.csv")
        lastDate = registry[registry['Execution'] == "COMPLETED"].tail(1)['Date'].iloc[0]
        lastDate = datetime.strptime(lastDate, "%H:%M:%S %d/%m/%Y")
        today_date = datetime.now()
        diference = today_date - lastDate
    except (IndexError, FileNotFoundError) as e:
        diference = timedelta(days=0)


    #Check if IBKR Portfolio already exists
    if ("Cartera1" not in driver.page_source):
        portfolio_initiation()


    elif (diference > timedelta(days=7)): 
        print("More than 7 days have passed since previous execution, restarting portfolio")

        delete_portfolio("Cartera1")
        delete_portfolio("Cartera2-Largo")
        delete_portfolio("Cartera3-Corto")
        
        portfolio_initiation()

    else:
        process_portfolio("Cartera1", transactions)
        time.sleep(6)

        #print(df_cartera2_transactions)
        if df_cartera2_transactions.empty == False:
            df_cartera2_transactions["Time"] =  pd.to_datetime(df_cartera2_transactions["Time"], format="%Y-%m-%d  %H:%M:%S")
            df_cartera2_transactions["Quantity"] = df_cartera2_transactions['Quantity'].astype(int)
            process_portfolio("Cartera2-Largo", df_cartera2_transactions)

        if df_cartera3_transactions.empty == False:
            df_cartera3_transactions["Time"] =  pd.to_datetime(df_cartera3_transactions["Time"], format="%m/%d/%Y")
            df_cartera3_transactions["Quantity"] = df_cartera3_transactions['Quantity'].astype(int)
            process_portfolio("Cartera3-Corto", df_cartera3_transactions)

    driver.close()
    print("Automatic Task at Investing.com completed")

def get_driver():
    return driver

