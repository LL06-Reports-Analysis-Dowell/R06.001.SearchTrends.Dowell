import pandas as pd
import numpy as np
import socket #To check available ports and check internet connection
import time
from contextlib import closing #close the port after checking
from selenium import webdriver #web scraping
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys#Input of keys
from selenium.common.exceptions import NoSuchElementException
import datetime
import pychrome#chrome developer tools neeeded to simulate geolocation
from pymongo import MongoClient #Connect with MongoDB

class myClass:
    def __init__(self):
        self.hostname = "one.one.one.one" #DNS port to check the internet connection
        self.options = webdriver.ChromeOptions()
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.22 Safari/537.36' #User-agent is used to give information to server request made from which platform/OS
        self.port_number = self.find_free_port() #Calling function to check availables port on localhost to run the chrome instance on
        self.port_url = "--remote-debugging-port=" + str(self.port_number) #Use the available port number to assign to chrome instance
        self.options.add_argument(f'user-agent={self.user_agent}') #User agent is added
        self.options.add_argument(self.port_url) #Port is given
        self.options.add_argument("--disable-renderer-backgrounding")#Set the priority(low, medium, high) of chrome instances(Generally runs on low but using this, it runs on Medium priority)
        self.options.add_argument("--disable-dev-shm-usage")#Handles chrome instance crash
        self.options.add_argument("--disable-gpu")# Temporarily needed if running on Windows
        self.options.add_argument("--disable-features=VizDisplayCompositor")#Time out error
        self.options.add_argument("--headless")#Open headless chrome instance
        self.options.add_argument("--no-sandbox")#Required to efficiently open headless chrome
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(), chrome_options=self.options
        )#New chrome instance is opened
        self.url = "http://localhost:" + str(self.port_number)#localhost string and port number to assign to pychrome so that we can use chrome developer tools and everything with separate instances on different port numbers(Each instances is separate from the others)
        self.dev_tools = pychrome.Browser(url=self.url)#enables dev_tools to use on each instance
        self.tab = self.dev_tools.list_tab()[0]#[0] represents first tab in every chrome instance
        self.tab.start()#=starts the tab
        self.driver.get("https://www.google.com/search?q=a&hl=en")#Change to the page to change geolocation(CLick on 'Update Location' or 'Use precise location')
    def is_connected(self):#To check the internet conncetion
        try:
            host = socket.gethostbyname(self.hostname)
            s = socket.create_connection((host, 80), 2)
            s.close()
            return True
        except:
            return False

    def loop_connected(self):#This function is called to check the internet connection thruoghout the code which will call is_connected() 
        if self.is_connected(): #If internet connection is there, it will return True and remaining code will continue
            return True
        else:#If false, it will wait 10 seconds for internet connection and try again
            print("Internet Disabled")
            time.sleep(10)
            self.loop_connected()#Call itself again

    def find_free_port(self):#Use to find free ports on localhost
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    def set_location(self, latitude, longitude):#Used to simulate the geolocation
        self.loop_connected()#Check internet connection
        self.tab.call_method("Network.enable", _timeout=20)
        self.tab.call_method("Browser.grantPermissions", permissions=["geolocation"])#Give access to access the location to chrome
        self.tab.call_method(
            "Emulation.setGeolocationOverride",
            latitude=latitude,
            longitude=longitude,
            accuracy=100,
        )#This will change the location to given geolocation
        time.sleep(15)#Need to wait to change the geolocation
        try:
            self.bodyText = self.driver.find_element_by_tag_name("body").text#Check whether'Use precise location' or 'Update Location' Exist in text and also check if it's empty
            if self.bodyText != None:#If page is loaded
                if "Use precise location" in self.bodyText:#If 'Use precise location' is there, it will click on it
                    self.driver.find_element_by_xpath("//a[text()='Use precise location']").click()#Click on 'Use precise location'
                    time.sleep(3)
                    return True
                elif "Update location" in self.bodyText:#If 'Update location' is there, it will click on it
                    self.driver.find_element_by_xpath("//a[text()='Update location']").click()
                    time.sleep(3)
                    return True
                else:
                    print('Send mail')
        except NoSuchElementException:#If page is not loaded proparly
            self.loop_connected()
            self.driver.refresh()#page will refresh
            time.sleep(5)
            self.bodyText = self.driver.find_element_by_tag_name("body").text
            if self.bodyText != None:
                if "Use precise location" in self.bodyText:#If 'Use precise location' is there, it will click on it
                    self.driver.find_element_by_xpath("//a[text()='Use precise location']").click()
                    time.sleep(3)
                    return True
                elif "Update location" in self.bodyText:#If 'Update location' is there, it will click on it
                    self.driver.find_element_by_xpath("//a[text()='Update location']").click()
                    time.sleep(3)
                    return True
                else:
                    print('Send email')#send mail
            else:
                return False
        except BaseException as error:#Handles All errors
            print('An exception occurred: {}'.format(error))
            return False

    def change_language_settings(self,language):#Used to change browser language/Chrome settings
        language_link = 'https://www.google.com/?hl='+str(language)#Values such as (en,hi,ta) is given
        self.driver.get(language_link)#Change the language

    def separate_alphabets(self, letter):
        self.search_field = self.driver.find_element_by_name("q")#check if element 'q' is there which is for search bar
        self.autocomplete_list_of_a_letter = []
        self.letter = letter
        self.search_field.send_keys(str(self.letter))#Type the alphabet in search bar
        time.sleep(1.25)  #Wait for 1.25 seconds to autocomplete to come
        for self.loop in range(1, 11):#Fetching the autocomplete result
            try:
                self.li_items = self.driver.find_element_by_xpath(
                    "//*/ul/li[%d]/div/div[2]/div[1]" % (self.loop)
                ).text#Fetching all elements one by one from given xpath
                self.autocomplete_list_of_a_letter.append(self.li_items)
            except NoSuchElementException:#Handle the exception
                time.sleep(2)
                try:
                    self.li_items = self.driver.find_element_by_xpath(
                        "//*/ul/li[%d]/div/div[2]/div[1]" % (self.loop)
                    ).text#Doing the same things again after handling the excpetion
                    self.autocomplete_list_of_a_letter.append(self.li_items)#Appending to the temporary list
                except NoSuchElementException:#This exception is used because in some languages, few alphabets only have 4-5 autocomplete results, if we get the error here, we will append 'None' into the "autocomplete_list_of_a_letter" list for the rest of the positions after first 4-5 autocomplete words that we scraped
                    for self.inner_loop in range(self.loop - 1, 10):#This for loop with append 'None', refer the comment above
                        self.autocomplete_list_of_a_letter.append(None)
                    break
        self.driver.find_element_by_name("q").clear()#Empty the search bar
        return self.autocomplete_list_of_a_letter#return the result to the retrieving_alphabets

    def retrieving_alphabets(self, alphabets):#Alphabets list is given
        self.alphabets = alphabets
        self.json_letters = {}
        for self.i in range(len(self.alphabets)):#Iterate through each alphabet
            self.json_letters[self.alphabets[self.i]] = self.separate_alphabets(
                self.alphabets[self.i]
            )#Calls separate_aplhabets() to retrieve autocomplete results for each alphabet
        return self.json_letters
