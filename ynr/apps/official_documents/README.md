# Ballot and Election SOPNs

There are two high level concepts for how SOPNs (Stetements of Person's 
Nominated) are stored:

1. A single document contains information about a single ballot
2. A single document contains information about more than one ballot


This application stores both types of document.

## ElectionSOPN

This stores multi-ballot SOPNs. Each `ElectionSOPN` have multiple 
`BallotSOPNs`. These are matched either automatically or manually and the 
matching pages are split up and stored as `BallotSOPNs`. 


## BallotSOPN

A `BallotSOPN` stores information about a single ballot. It can have more 
than one page, if the candidates table spans more than one page, but it 
never contains information about more than one ballot. 

If the original document was a multi-ballot SOPN then this will contain only 
the pages of the PDF that relate to this ballot.   
