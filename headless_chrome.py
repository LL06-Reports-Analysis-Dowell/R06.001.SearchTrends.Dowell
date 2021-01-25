from Automated_version_3 import myClass#Use the Autocomplete_version_3 where all the functions required are created
import pandas as pd
import numpy as np
import datetime
import time
import gspread#To handle google spreadsheet(Not required after master data is shifted to MongoDB)
from pymongo import MongoClient#Work with monogDB
import itertools#Used for multi-threading
from multiprocessing.dummy import Pool as ThreadPool #Used for multi-threading
import multiprocessing#Used for multi-threading
from itertools import repeat#Used for multi-threading
from bson import ObjectId#Convert the string to mongodb object_id format


def get_city_info():#Retreiving the sheet 'ALL_City' from spreadsheet called 'India_Master' which is used as master table
    all_city = sh.worksheet("ALL_City")
    temp = all_city.get()
    city_info = {}
    for x in range(len(temp)):
        if temp[x][0]==city:
            city_info = temp[x]
    return city_info#returns the information about cities stored

def get_city_languages_from_sheet(city):#Retreiving information from separate city sheets available on spreadsheet 'India_Master' City sheet
    city_sheet_name = city+"_Language"
    city_sheet_from_googlesheets = sh.worksheet(city_sheet_name)
    temp_1 = city_sheet_from_googlesheets.get()
    df1 = pd.DataFrame(temp_1,columns=temp_1[0])
    df1 = df1.drop(labels=0).reset_index()
    df1.drop(['index'],axis=1,inplace=True)
    return df1#Languages dataframe for a given city is returned

def converting_string_to_list(string_of_languages):#Convert the string to list
    return string_of_languages.strip('][').split(',')

def storing_in_mongodb(language,browser_language,autocomplete,id_of_object):#Used to store retrieved autocomplere results in mongoDB
    global collection_name
    combination_name = "Autocomplete."+ str(language)+"."+str(browser_language)# English_en, English_hi
    rec={
            "Hour": str(datetime.datetime.now().strftime("%I")) + str(datetime.datetime.now().strftime("%p")),
            str(combination_name): autocomplete#geolocation
    }#This will be updated in existing document
    collection_name.update_one({'_id':id_of_object},{"$set":rec})#Update the document


def write(i,obj,combination,lat,log,id_of_object,city,data_frame):#This fucntion will run in paralled using multi-threading
    time.sleep(i)
    print(i, "---", obj,"---",combination)
    flag = obj.set_location(lat,log)#Each instance will be working indepedently to change the location from Automated_version_3.py
    if flag:
        obj.change_language_settings(combination[1])#Change the browser language from Automated_version_3.py
        name = str(combination[0]) + "_binary"
        language_array = np.array(data_frame[data_frame[name]=='Yes'][combination[0]])#Fetch the Alphabet list for given language from dataframe
        result = obj.retrieving_alphabets(language_array)#The list of alphabet is given to Automated_version_3.py function which will give us the result of All scapred autocomplere words for each alphabet
        storing_in_mongodb(combination[0],combination[1],result,id_of_object)#Call the storing_in_mongodb() fucntion to store the fetched autocomplete result
        obj.driver.close()#Close the chrome driver
        obj.driver.quit()#Close the driver
    else:
        obj.driver.close()#Close the chrome driver
        obj.driver.quit()#Close the driver

if __name__ == '__main__':    
    city='Delhi' #Needs to be variable
    client = MongoClient("mongodb+srv://vaibhav:Password@cluster0.kfdbs.mongodb.net/test?retryWrites=true&w=majority")#Connection string for mongoDB
    database_name = client.Autocomplte_results#Select database
    collection_name = database_name[city]#Select document
    gc = gspread.service_account(filename="rising-area_credential.json")#Credential to access the spreadsheet without authorization everytime(This JSON file is required to fetch the data from google spreadsheet)
    sh = gc.open("India_master")#Name of the sheet
    values_list = get_city_info()#Retrieve the 'ALL_City' sheet as one read
    language_dataframe = get_city_languages_from_sheet(city)#NEw dataframe where all columns of languages will be there fetched from the spreadsheet
    latitude,longitude = float(values_list[4]),float(values_list[5])#Getting latitude and longitude information form the spreadsheet
    languages = converting_string_to_list(values_list[1])#Convert the Languages string stored in spreadsheet to list 
    languages_abbreviation = converting_string_to_list(values_list[2])#Convert the Browser Languages string stored in spreadsheet to list 
    combinations = list(itertools.product(languages, languages_abbreviation))#Combination of above two(4*4=16)
    list_of_numbers = list(range(0, len(combinations)))#Needed to synchronize the time and present the list of instances running
    list_of_objects = []
    for j in range(len(combinations)):
        list_of_objects.append(myClass())#Open chrome instances equaled to number of combinations of language and browser language
    pool = ThreadPool(len(combinations))#Creates threads equaled to number of combination
    rec={
            "City": city,
            "Month": datetime.datetime.now().strftime("%b"),
            "Date": str(datetime.datetime.now()).split(' ')[0],
            "State":values_list[3]
    }#Create a new mongoDB document data
    object_id = collection_name.insert_one(rec).inserted_id#New mongoDB document, Object id is fetched of the newly created document and passed through all threads
    pool.starmap(write, zip(list_of_numbers,list_of_objects,combinations,
                      repeat(latitude,len(combinations)),repeat(longitude,len(combinations)),repeat(object_id,len(combinations)),
                            repeat(city,len(combinations)),repeat(language_dataframe,len(combinations))))#This will handle all multi-threaded operations, "zip" is used to pass variables to all threads, (list_of_numbers,list_of_objects,combinations) will be iterated element by element, "repeat" send the same value to all thread and chrome instances(latitude,longitude,object_id,city,language_dataframe) are constant among all threads
    pool.close() #Close the thread pool
    pool.join() #Synchronization in excpetions
    client.close()#Close mongoDB client