var form = null
$(function() {
    // avoids running this on every page
    form = document.querySelector("#ballot_paper_results_form")
    if (!form) { return; }

    tiedWinners() 
    $('*[id*=id_memberships]').on("change", tiedWinners)

    if($(".errorlist").length != 0){
        tiedWinners() 
    }
})

function removeCoinTossFields(voteCountInputs) {
    for (var i = 0; i < voteCountInputs.length; ++i) {
        voteCountInputs[i].nextElementSibling.style.display = "none"
        voteCountInputs[i].nextElementSibling.querySelector("*[id*=id_tied_vote_memberships]").checked = false
    }
}

function tiedWinners() {
    var voteCountInputs = document.querySelectorAll('*[id*=id_memberships]')
    var list = Object.values(voteCountInputs)
    var ballotWinnerCount = form.dataset.winnerCount

    // array of integers representing the vote count for each candidate,
    // sorted lowest to highest
    var voteCounts = list.map(input => parseInt(input.value)).sort(
        function(a, b) {
            return a - b;
        }
    );

    // wait until all inputs are completed before showing any coin toss fields
    if (voteCounts.includes(NaN)) {
        return removeCoinTossFields(voteCountInputs);
    }

    // get an array of the winning vote counts e.g. if the ballot has a winner
    // count of 2, the last 2 vote counts from the sorted array of vote counts
    var winningVoteCounts = voteCounts.slice(-ballotWinnerCount)
    // loop through all the candidates to build a array of winners
    var winners = []
    for (var i = 0; i < voteCounts.length; ++i) {
        var candidateVoteCount = parseInt(voteCountInputs[i].value)
        if (winningVoteCounts.includes(candidateVoteCount)) {
            winners.push(voteCountInputs[i]);
        };
    }

    // if the number of winners is the same as the ballots winner count,
    // no need for any coin toss tiebreakers
    if (winners.length == ballotWinnerCount ) {
        removeCoinTossFields(voteCountInputs)
    // otherwise we have some winners with tied vote counts
    } else {
        // find the lowest winning vote count
        var lowestWinningVoteCount = winningVoteCounts[0]
        for (var i = 0; i < winners.length; ++i) {

            // if the vote count of this candidate is higher than the lowest
            // then they dont need a coin toss, skip them
            if (parseInt(winners[i].value) > lowestWinningVoteCount) {
                continue;
            }
            // otherwise show the coin toss field for this candidate
            winners[i].nextElementSibling.style.display = "inline";
            }
    }
}