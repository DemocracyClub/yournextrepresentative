
$(document).ready(function() {
    $('#ballot_paper_results_form').on('change', function() {
 
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
            for (var i = 0; i < inputArray.length; ++i) {
                var max = 0;
                max = Math.max(...inputArray);
                var maxIndex = list.indexOf(max)
                
                if (maxIndex != inputs[i] && max == inputs[i].value) { 
                    if (inputs[i].value == max) {
                        inputs[i].nextElementSibling.style.display = "inline"
                    } else {
                        inputs[i].nextElementSibling.style.display = "none" 
                    } 
                } else {
                    return
                }
            }
        }
    })
})