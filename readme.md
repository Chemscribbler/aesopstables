# WIP on Reimplementing what became Aesop's Tables
https://github.com/Chemscribbler/sass

Ultimate goal is to have a super easy to deploy (heroku or heroku like)

For now to get it started:

install requirements using `pip install -r requirements.text`

then run:
`flask db init`
`flask db migrate`
`flask db upgrade`

and then to interface with an environment where the datatables are pre-loaded you can use
`flask shell`

You will still need to import utility functions
