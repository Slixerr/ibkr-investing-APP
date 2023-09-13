from datetime import datetime
import os
import time
import pandas as pd
import pyautogui
import ctypes
import projectIBKR as pr
import investingAuto as inv


with open("userCredentials.txt", 'r') as file:
    for line in file:
        if 'userIBKR' in line:
            userIBKR = line.strip().split('=')[1].strip()
        elif 'passIBKR' in line:
            passIBKR = line.strip().split('=')[1].strip()



# Necessary variables to ensure continious execution
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

# Prevent system shutdown
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

#Create folder Datos if doesn't already exist 
os.makedirs('Datos', exist_ok=True)

if os.path.exists('Datos/registry.csv'):
    registry = pd.read_csv('Datos/registry.csv')
else:
    registry = pd.DataFrame(columns=["Execution", "Date", "ErrorMessage"])

try:
    print('Executing projectIBKR.py')
    os.startfile(r'C:\Jts\tws.exe')

    
    time.sleep(10)

    pyautogui.typewrite(userIBKR)
    pyautogui.typewrite(["tab"]) 
    pyautogui.typewrite(passIBKR)
    pyautogui.typewrite(["enter"]) 
    time.sleep(25)
    pyautogui.click(x=61, y=53)
    pyautogui.click(x=103, y=274)
    time.sleep(2)
    pyautogui.getWindowsWithTitle("Interactive")[0].minimize()
    pyautogui.getWindowsWithTitle("Operaciones")[0].minimize()
    pr.generate_portfolio()
    pr.generate_transactions()
    pyautogui.getWindowsWithTitle("Interactive")[0].close()



    print('Executing investingAuto.py')
    #exec(open('investingAuto.py').read())
    inv.main_investing()

    new_df = pd.DataFrame({
            "Execution": ["COMPLETED"],
            "Date": [now],
            "ErrorMessage": [""],
        })
    registry = pd.concat([registry, new_df], ignore_index=True)
    print("Script correctly executed")
        
except Exception as e:
    new_df = pd.DataFrame({
            "Execution": ["ERROR"],
            "Date": [now],
            "ErrorMessage": [str(e).split('\n')[0]],
        })
    registry = pd.concat([registry, new_df], ignore_index=True)
    print("Error in script: " + str(e))


registry.to_csv("Datos/registry.csv", index=False)


#Restore ability to shutdown
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)




