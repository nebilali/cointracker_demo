# Cointracker Demo


## Description
This is a simple api server which supports adding/removing accounts and looking at account balances and transactions. Balances and transactions will be updated with the `sync` endpoint.

## API Endpoints
- POST /address/add
	- This end point will add addressess to the DB
	- Expected query param inputs are:
		- account_ids: string of accounts to query deliminated by `|`
	- Example:
		```
		curl -X POST http://127.0.0.1:5000/address/add?account_ids='14A2w5ChYSYfT5GvQ4oN2j2mrfsQxRXcvJ|3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd
		```
- DELETE /address/remove
	- This endpoint will remove address from the DB and also remove associated transactions.
	- Expected query param inputs are:
		- account_ids: string of accounts to query deliminated by `|`
	- Example:
		```
		curl -X POST http://127.0.0.1:5000/sync?account_ids='14A2w5ChYSYfT5GvQ4oN2j2mrfsQxRXcvJ|3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd
		```
- GET /address/balance
	- This endpoint quries the DB to get the balance of added accounts. It should raise an exception if querying account_ids that have not been added. This will return a map of all input accounts to their balance and the total balance of all queried accounts.
	- Expected query param inputs are:
		- account_ids: string of accounts to query deliminated by `|`
	- Example:
		```
		curl -X GET http://127.0.0.1:5000/address/balance?account_ids='14A2w5ChYSYfT5GvQ4oN2j2mrfsQxRXcvJ|3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd
		```
- GET /transaction
	- Will read transactions from the DB for added accounts. 
	- Expected query param inputs are:
		- account_ids: string of accounts to query deliminated by `|`
		- limit: max number of transactions to return. Defaults to unlimited
		- offset: if set to `n` will start at the `nth * limit` transaction (sorted in decending order by block height). i.e offset = 2 and limit = 10 will get the 20th - 30th transactions.
	- Example:
		```
		curl -X GET http://127.0.0.1:5000/transactions?account_ids='14A2w5ChYSYfT5GvQ4oN2j2mrfsQxRXcvJ|3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd'

		curl -X GET http://127.0.0.1:5000/transactions?account_ids='14A2w5ChYSYfT5GvQ4oN2j2mrfsQxRXcvJ|3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd&limit=10&offset=2'
		```
- POST /sync
	- Endpoint will use third party API to get transactions for each input account id and update the db for the transactions and balance of the account. Third party API will be used to grab transactions up to the block queried in the last sync, update the DB with the new transactions, calculate the delta in the balance from the new transactions, and update the balance with the delta. Note this enpoint will call the third party api multiple times in many cases. This can be intensive for accounts with many transactions on the initial sync and can be prone to being throttled.
	- Expected query param inputs are:
		- account_ids: string of accounts to query deliminated by `|`
	- Example:
		```
		curl -X POST http://127.0.0.1:5000/sync?account_ids='14A2w5ChYSYfT5GvQ4oN2j2mrfsQxRXcvJ|3E8ociqZa9mZUSwGdSmAEMAoAxBK3FNDcd'
		```

## Design Choices
1.) Database 
	- I've created an accounts an transactions table. In both tables I've decided to represent account and transaction hashes as text strings. I originally approched representing the hashes has numbers because it would allow for a fixed storage size and would be smaller then would take less space then representing them as a string. I decided to stick with strings for this mvp, for simplicity and readability.
	- I also debated wheather or not to us DB since we can get all the data by just using the third party api and not have to worry about syncing. I ended up using the DB because:
		1.) There is a throttling limit when using these APIs and it won't be scalable under heavy load, 
		2.) We are charged per request when making API queries and just storing previously processed transactions would save on operating costs.
		3.) User tx data is publicly availible on the block chain. I don't feel any conflict in terms of data ownership here. We can add some features to allow users to remove their data if they want. 		
2.) I wanted to make sure that we update account balance through tx data instead of querying for it directly. This is for a number of reasons:
	1.) We are going to need to get tx data anyway
	2.) This lends itself to incremental update of the balance which is important for a number of follow up features such as allowing user to selectively add/remove transactions (also why I chose to store the value_change in the transactions table scheme), and continuous background syncing is a pretty straight forward next step. 


## Things to improve in production
- I'd like to store the DB entries as an object that would be consistenlty used throughout our code base, likely a protocol buffer. 
- This API server seemed to be directly called by the client so maybe straight http makes sense for a request/response framework. If this is to be more of a backend api server, I would lean towards using gRPC.
- I ran out of time before implementing thorough unit tests, but this is something I was thinking about when starting out. The __init__.py file is setup to point to a test DB through configuration and that would be create for injecting a test DB when needed.
- I also ran out of time before implementing the background sync feature. This would basically be a continuously running job that checks the transactions published in the next block against accounts that are added in our table and if it finds any it would initiate the sync endpoint on those accounts. The incremental cost here should be relatively cheap as we will be updating the transaction table greadily and the rate of new blocks being mined is graciously slow.
- I used absl for logging. I know flask has some internal libraries for logging. I just stuck with absl because it is was I know and it saved me some time.

## Challanges
- This took me a bit longer to ramp up than I enticipated. By that I mean setting up an environment and to relearn some of the python libraries such as flask and absl.
- I was getting inconsistent results when testing locally on accounts with large transactions. I believe this is because my ip address was getting throttled for using the api to heavily and this stalled me for a bit.


## Set up
1. Go into cointracker_demo directory
2. Run set_up.py file.
	- ```source set_up.py```
	- This is initalize the database and sets the env director.
3. Start the server
	-```flask run```


