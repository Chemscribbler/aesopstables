# How to Use Aesop's Table

Many of the features are currently live and working as intended. The first thing that should go out of date here is the Admin page, which I'm rushing to get properly setup.

## Creating an Account

In the login page there is a link to register. Register with a username and email you are comfortable with potentially being accessible. Passwords are hashed, but I am not hashing usernames/emails at the moment. You can put anything in the email field as it currently doesn't do anything, but eventually I'd like to do password reseting via email.

If you do lose your password reach out to me on Discord/Slack

## Creating a tournament

Creating a tournament, on the homepage there is a create tournament button. Enter the Title you want displayed for your tournament. This is currently un-editable, but that is something that I can fix for now, before I automate it. You must be logged in to create an event.

## Registering players

Your tournament url with be something like aesopstables.net/# where the number is the ID for your tournament. This is probably the best link to send your players as it includes a button so they can register themselves. If they don't want to, you can click that button, or go to aesopstables.net/#/register to register players. Currently I am getting the ID list from [NRDB](https://netrunnerdb.com/). IDs should refresh within 24 hours of new cards. IDs are not required.

## Admin View

If you are logged in and the tournament creator, you will see a bunch of additional UI elements that allow you to control the event. Whenever you're ready you can pair the round. To unpair a round, or manually adjust the pairings, you do so from the round page, which is just under the *Round* header. Currently I'd recommend only unpairing rounds starting from the highest numbered (most recent) round and working your way down.

### Recommendations for Number of Rounds and Cut Size

Once Round 1 is paired, it's important to determine the appropriate number of rounds for your tournament based on the number of players. Below is a recommendation for the number of rounds and cut size for different player counts in Single Sided Swiss Events (both Casual and Competitive):

#### Single Sided Swiss Events: Casual

| Players | Swiss Rounds | Cut                   |
| ------- | ------------ | --------------------- |
| < 16    | 5-6          | None                  |
| 16-36   | 6            | Top 4 Double Elim     |
| 37-63   | 7            | Top 8 Double Elim     |
| 64-146  | 8            | Top 8 Double Elim     |
| 147-219 | 10           | Top 8 Double Elim     |
| 220+    | 12           | Top 16 Double Elim    |

#### Single Sided Swiss Events: Competitive

| Players | Swiss Rounds | Cut                   |
| ------- | ------------ | --------------------- |
| < 16    | 5-6          | None                  |
| 16-24   | 6          | Top 4 Double Elim     |
| 25-64   | 6-7           | Top 8 Double Elim     |
| 65-146   | 8           | Top 8 Double Elim     |
| 147-219   | 10           | Top 16 Double Elim    |
| 220+     | 12           | Top 16 Double Elim    |

Editing the round - once the round is made you can delete matches to get players into an unpaired pool. Then you can create tables however you'd like. Please be careful, I haven't written any code preventing someone from playing multiple matches in one round.

## Undo Pairings & Close the Round

For now this deletes all pairings. If you hit the pairing button, it should make the same (or very similar) pairings. However the most likely reason you're undoing a pairing is because a result changed. In that case, change the result, then on the admin panel for any round but the one you were doing the pairing for, hit close round. That should recalculate everyone's scores.

## Getting ABR Results

At the bottom of the main page for the tournament is a Export to ABR button. This will download a json for you. Then go to ABR and conclude the tournament and upload the json in the field.

# Future Features

These are all at various stages of development (almost all ideation) - if there is one that makes a big difference in your interest in the tool please reach out!

- Recommend number of rounds and cut size in the UI
- Fix json export (currently cannot get match information)
- More control of registration and match reporting (aka only TO can register players or report results)
- Players register with decklists (revealed in cut)
- First round byes
- Cut visualization (looking for help)
- Stats panel - breaking down ID popularity and winrates
- Arbitrary number cuts (looking for algorithm help)
- Make manual pairing less ugly
