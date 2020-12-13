# Origin Markets Backend Test

### Spec:

We would like you to implement an api to: ingest some data representing bonds, query an external api for some additional data, store the result, and make the resulting data queryable via api.
- Fork this hello world repo leveraging Django & Django Rest Framework. (If you wish to use something else like flask that's fine too.)
- Please pick and use a form of authentication, so that each user will only see their own data. ([DRF Auth Options](https://www.django-rest-framework.org/api-guide/authentication/#api-reference))
- We are missing some data! Each bond will have a `lei` field (Legal Entity Identifier). Please use the [GLEIF API](https://www.gleif.org/en/lei-data/gleif-lei-look-up-api/access-the-api) to find the corresponding `Legal Name` of the entity which issued the bond.
- If you are using a database, SQLite is sufficient.
- Please test any additional logic you add.

#### Project Quickstart

Inside a virtual environment running Python 3:
- `pip install -r requirements.txt`
- `./manage.py runserver` to run server.
- `./manage.py test` to run tests.

#### API

We should be able to send a request to:

`POST /bonds/`

to create a "bond" with data that looks like:
~~~
{
    "isin": "FR0000131104",
    "size": 100000000,
    "currency": "EUR",
    "maturity": "2025-02-28",
    "lei": "R0MUWSFPU8MPRO8K5P83"
}
~~~
---
We should be able to send a request to:

`GET /bonds/`

to see something like:
~~~
[
    {
        "isin": "FR0000131104",
        "size": 100000000,
        "currency": "EUR",
        "maturity": "2025-02-28",
        "lei": "R0MUWSFPU8MPRO8K5P83",
        "legal_name": "BNPPARIBAS"
    },
    ...
]
~~~
We would also like to be able to add a filter such as:
`GET /bonds/?legal_name=BNPPARIBAS`

to reduce down the results. 

# Solution
Bonds can be listed, filtered and posted using the `/bonds/` path. 

For connecting to the GLEIF API, I have used the `requests` library. For mocking API calls in `tests.py`, I have used the `responses` library. Both libraries have been added as a dependency in `requirements.txt`. 

Each `Bond` is associated with a `User`, who created it and owns it. Each user can only see their own bonds. 

I have implemented user authentication following Django [REST Framework's authentication tutorial](https://www.django-rest-framework.org/api-guide/authentication/#api-reference). If you are interacting with the API through the browser, you can log into your user account from the *"Login"* button at the top right corner. 

Users can be registered via the admin console (at `/admin`/) or via a post request to `/registration/`. The registration endpoint was implemented consulting [this tutorial](https://nemecek.be/blog/23/how-to-createregister-user-account-with-django-rest-framework-api). 

All tests are defined in the `tests.py` file and split into categories. 