$(function() {
    tiedWinners() 
    $('*[id*=id_memberships]').on("change", tiedWinners)
   
    if($(".errorlist").length != 0){
        tiedWinners() 
    }
})

function tiedWinners() {
    var inputs = document.querySelectorAll('*[id*=id_memberships]')
    var list = Object.values(inputs)
    var inputArray = list.map(input => input.value)
    
    function NoneEmpty(inputArray) {
        if (inputArray.includes(""))
            return false
        else return true
    }
    
    var noEmptyValues = NoneEmpty(inputArray)
    if (noEmptyValues) {
        var max = Math.max(...inputArray);
        var winners = []
        for (var i = 0; i < inputArray.length; ++i) {
            if (inputs[i].value == max) { 
                winners.push(inputs[i])
            };
        }
        if (winners.length == 1 ) {
            for (var i = 0; i < inputArray.length; ++i) {
                inputs[i].nextElementSibling.style.display = "none" 
                inputs[i].nextElementSibling.querySelector("*[id*=id_tied_vote_memberships]").checked = false
            }
        } else {
            for (var i = 0; i < winners.length; ++i) {
                winners[i].nextElementSibling.style.display = "inline" 
             }
        }
    }
}