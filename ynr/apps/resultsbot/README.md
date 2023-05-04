# Results Automation 

## Overview

In this app, we have a collection of scripts that automate the process of generating results for many, but not all, elections in YNR.

## Usage

### `python manage.py create_mg_urls_file`

A csv with the modgov councils and urls will be created. This is the data that should be used to manually populate a google spreadsheet used in the next step.

### `python manage.py resultsbot_match_elections_for_mg_url`

Before running this step, make sure you've updated the google spreadsheet link with the correct election ids. This step will match the election ids to the modgov urls and save the results to a csv file.

There may be some elections that are not matched. There are a few reasons for this:

- The election does not use the modgov url election feature
- The election feature is enabled but the council hasn't used it yet. 

Given this second reason, you will need to follow this process a few times the day before elections, and then again on the day of elections, and the day after elections. This is because councils may enable the feature at any time.

There also may be more than one election in some cases. This is because the modgov url feature allows for multiple elections to be linked to one url. In this case, the script will present the user with a pick list of elections to choose from. Use the election ID presented in the pick list for clues. In the example below, given the election ID `local.basildon.2023-05-04`, the choice would be `57`:

```local.basildon.2023-05-04
https://www.basildonmeetings.info/mgManageElectionResults.aspx
Found more than one election for this date!
        56      Essex County Council By Election, Laindon Park and Fryerns Division
        57      Basildon Borough Council Election```






	





