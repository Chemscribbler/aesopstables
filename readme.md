Current repo for [aesopstables.net](http://www.aesopstables.net)

Program trying to run single sided swiss Netrunner events.

For now to get it started:

install requirements using `pip install -r requirements.text`

then run:
`flask db init`
`flask db migrate`
`flask db upgrade`

and then to interface with an environment where the datatables are pre-loaded you can use
`flask shell`

You will still need to import utility functions

Feature ToDos:
- Modernize backend to allow for a better control flow and less tight coupling of frontend to backend
- Enable match slips
- Incorporate first round byes
- Allow user logins to report their specific results
- User overall record tracking/global leaderboard
- Bracket visualization
- New coat of paint
