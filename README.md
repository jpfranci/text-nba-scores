# text-nba-scores
AWS Lambda Function to text NBA scores. 
Personally used when my data plan runs out and I want to keep track of my favorite nba team's games.

Usage:
`Scores` - Get scores across the NBA for today

`Scores <team_name>` - Get current score for specified team with top scorer data if they are playing right now. If not, returns the team's schedule.
Examples: Scores BOS/Scores Boston/Scores Celtics

To install:
Add as AWS lambda function to your account. 
Follow instructions in https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python-amazon-lambda to link AWS API Gateway to Twilio.
