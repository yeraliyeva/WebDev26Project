# Backend:
## Description 
func:
- auth
- typing levels
- leaderboard
- balance

non-func:
- working (optional)

---
auth:
- JWT

typing levels:
- 2 level type:
	- common typing
	- cat running 
- every level have it's own credits

leaderboard: 
- working (optional)
- on redis ZSET i think

balance:
- just balance

--- 

### services:
1. auth serivce - 100 RPS
2. level - 100 RPS
3. balance - 100 RPS
4. leaderboard - 100 RPS 

---

### schema:
1. proxy -> auth | give creds for login or refresh
 2. auth -> proxy | takes user_id and tokens
3. proxy <-> level, leaderboard, balance | proxy shares tokens and user_id to other services

after proxy we have DMZ that keeps security of everything, every request go to proxy after go to auth, goes through verification and after this goes to other services 

---
### tech stack:
proxy - traeffic
framework - DRF
db - postgre, redis
queue-kafka
cdc-debezium

---

## Auth

user can have profile image, but only predefined images that we already uploaded

access token lifetime is about 5 mins, 
refresh token lifetime is about 7 days,

endpoints:
`/auth/login` - for login
`/auth/registration` - for reg
`/auth/refresh` - to get new access token
`/auth/me` - to get info about user

User:
1. id : uuid
2. username : str
3. email : str
4. created_at : datetime
5. updated_at : datetime
6. password_hash : str
7. profile : ForeignKey(ProfileImage)

ProfileImage:
1. id: uuid
2. image_url: str

/login:
input:
{
	"login": str - username or email,
	"password": str
}
output:
{
	"user_id": uuid
	"access_token": str,
	"refresh_token": str
}


/registration:
input:
{
	"username": str - unique username,
	"email": str - unique email,
	"password": str - any password longer than 8 chars,
	"profile_image": uuid choosen image profile or none,
}
output:
Created user model without password hash


/refresh:
{
	"refresh_token": str - token for refresh,
}


/me: user_id from headers
output
User info 

debezium connects to user table and creates events in kafka if user registrated to create balance for user

---
## Level

service to get and submit attempts of levels

GET:  /level?start=N, limit=M - to get levels list and paginate through them
GET: `/level/{uuid}` - to get level data
POST: `/level` - to submit

Level:
1. id : uuid
2. text: str - level text
3. cost: int - level credits cost
4. goal_wpm - level goal wpm
5. created_at
6. updated_at

Submit:
1. id: uuid
2. level_id: ForeignKey(Level.id)
3. user_id: ForeignKey(User.id)
4. wpm: int - user_wpm
5. rewarded_credits: int - min(1, goal_wpm/user_wpm ) * level_full_cost | IF USER ALREADY HAVE SUBMIT OF THIS LEVEL WE GIVE 0 CREDITS
6. created_at: datetime

/level/{uuid}
input:
...
output:
Level info

/level:
input: somehow get user_id from headers
{
	wpm: int, 
	level_id: uuid,
}


debezium connects to submit table and after every submit with >0 amount reward creadits creates event in kafka to give user reward in balance service

---

## Balance 

service to work as users wallet and contain their balance


we read from kafka to events like create balance or give reward, we cannot get transactions or any action from somewhere else

endpoints:
GET: `/balance/{user_id}` - to get current user balance
GET: `/transactions/{user_id?start=N, limit=M` - to view transactions list and paginate through them


Balance:
1. id: uuid
2. user_id: ForeignKey(User.id)
3. balance: int | Never negative
4. updated_at: datetime

NOTE: make +/- not in python but via SQL or ORM thing on database level with atmomicity

Transaction:
1. id: uuid
2. event_id: uuid
3. amount: int
4. type: DEBIT | CREDIT # debit it's minus balance, credit it's plus balance
5. created_at: datetime

every transactions event_id should be unique, cause we get it from kafka, and in kafka event it's from submit, so one submit one reward, also it's for idempotency 

---
## Leaderboard

Service to have a users leaderboard by balance for this day 

i think top would be like for 10 users but build like we can easily change everything later

Use Redis ZSETS 
set in format:
```
ZADD leaderboard:daily 125 "user_773"
```

get top 10 using this:
```
ZREVRANGE leaderboard:daily 0 9 WITHSCORES
```

get for specific user:
```
ZREVRANK leaderboard:daily "Rauan"
```

endpoints:
GET `leaderboard/`
input: get user_id from headers
...
output:
{
top:[
{place: 1, username: ..., user_id: ...}
{place: 2, username: ..., user_id: ...}
{place: 3, username: ..., user_id: ...}
...
],
user_place: int,
}

