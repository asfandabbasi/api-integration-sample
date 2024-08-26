# EdgeTier Integration Challenge

**Note:** Please do not put your solution in a public repository (GitHub etc.). We are sending this to multiple candidates and do not want anyone to have an unfair advantage.

This task should hopefully only take you 2 or 3 hours to complete.  

# Introduction

At EdgeTier, we build and maintain lots of integrations with customer support software (such as Zendesk, Salesforce, Kustomer, LiveChat etc.). In this assignment, we would like you to build a small integration into a fake chat system called BigChat.  

## Setup

* Install Python 3.11+.
* Install SQLite. Mac already has this installed already most of the time.
* `git clone` the repository.
* Create a virtualenv.
* `pip install -r requirements`.

## Running

* Start OurAPI:
  * `cd our_api`
  * `uvicorn main:app --port 8266` (inside virtualenv) 
* Start BigChat:
  * `cd big_chat`
  * `uvicorn main:app --port 8267` (inside virtualenv) 

## BigChat API

BigChat is a fake live chat service. It's API returns one of four events:

* `START`: When a chat starts.
* `END`: When a chat ends.
* `MESSAGE`: When a customer or agent sends a message.
* `TRANSFER`: When a chat is transferred from one agent to another.

When the app is running, you can find the documentation here: http://127.0.0.1:8267/docs.

## Our API

OurAPI is EdgeTier's main API. Send it chats, agents, and other details. 

When the app is running, you can find the documentation here: http://127.0.0.1:8266/docs.

## Task

Create an integration between BigChat API and Our API. Write a script that calls BigChat's `/events` route every 10 seconds (to get the latest events in the last 10 seconds) that will create/edit chats and agents in OurAPI as needed. Feel free to edit anything inside `/integration`. Add as many files or whatever structure you want. We would recommend writing tests as well.

Please do not edit anything inside `/big_chat` or `/our_api`, assume they are APIs that can't be changed.
