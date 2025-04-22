### ResultSet

The ResultSet object relates to the ballot results (not elected candidates which is on the Candidate model) is created through a form populated with data from a user with permissions. The ResultSet form is used to collect the following data:

#### `num_turnout_reported`: 
- accepts a positive integer
- verbose_name="Reported Turnout (Number, not required)
- help_text="The number of people who voted in this election"
- This field only accepts a whole number, but accepts commas and cleans them 
on input for the user

#### `turnout_percentage`: 
- accepts a Float
- validates a minimum value of 0 and a max of 100
- verbose_name="Turnout Percentage"
- help_text="The percentage of the electorate who voted in this election"
- this is automatically calculated by dividing the number of ballots cast by the total electorate if those fields are populated, otherwise accepts a float and will round to two decimal places

#### `num_spoilt_ballots`: 
- accepts a postive integer
- verbose_name="Spoilt Ballots"
- help_text="The number of spoilt ballots in this election"
- This field only accepts a whole number, but accepts commas and cleans them 
on input for the user

#### `total_electorate`: 
- acceptes a positive integer
- verbose_name="Total Electorate", aka `num_ballots`
- help_text="The total number of people eligible to vote in this election"
- This field only accepts a whole number, but accepts commas and cleans them 
on input for the user


#### `source`: 
- accepts text 
- verbose_name="Source"
- help_text="The source of the data for this result"
- this is a free text field that is required (validation included) to verify the above data