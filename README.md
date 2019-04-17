# ChatBot for stock market
This chatbot is able to provide user real time and historical stock stock information. Through Wechat, user can talk to the chat bot and get the information about a specific target they want. If ambiguous company name are provided, user has to speciy one of the selections of qualified stocks.
## Example
![demo_3](https://user-images.githubusercontent.com/42895408/56313987-e11b7980-6121-11e9-83a4-b05f6029616f.gif)
# Prerequisites
There are several packages you need to install in order to set up the environment.
### RASA NLU
The recommended way to install Rasa NLU is using pip which will install the latest stable version of Rasa NLU:
```
pip install rasa_nlu
```
Also make sure spacy_skearn are embeded.
```
pip install rasa_nlu[spacy]
python -m spacy download en_core_web_md
python -m spacy link en_core_web_md en
```
### dateutil
dateutil can be installed from PyPI using pip (note that the package name is different from the importable name):
```
pip install python-dateutil
```
### wxpy
wxpy supports Python 3.4-3.6 and 2.7. 
```
pip install -U wxpy
```

# Common Usage Example
### Real-time information (open, close, high, low price and volume) 
![demo_3](https://user-images.githubusercontent.com/42895408/56313987-e11b7980-6121-11e9-83a4-b05f6029616f.gif)
### Historical Data (open, close, high, low price and volume at specific date or during a period of time)
#### Check information at a specific date
![demo1](https://j.gifs.com/k8roM6.gif)
#### Check information during a period of time
![demo2](https://j.gifs.com/mOYE09.gif)
#### Multi turn response
![demo_4](https://user-images.githubusercontent.com/42895408/56314137-38b9e500-6122-11e9-94af-1989e1bcc89e.gif)

# Deployment
In order to deploy this program on your computer, you need to download all files in a same folder with all packages mentioned above installed.   
Change the following lines to make your target user able to the program. You can make it by simply substute "ask" with your users' name.  
```
user = bot.friends().search("ask")[0]
```
Run the program and log in your Wechat account by scanning the generated QR code.
# Authors
* Chuwen Song  
email: songc5@rpi.edu
