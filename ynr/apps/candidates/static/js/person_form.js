"use strict";
var BALLOT_INPUT_CLASS = "input.js-ballot-input:not(:hidden)";
var PARTY_WIDGET_SELECT_CLASS = "select.party_widget_select";
var PARTY_WIDGET_INPUT_CLASS = "input.party_widget_input";
var PARTY_LIST_POSITION_INPUT_CLASS = "input.party-list-position";
var BALLOT_GROUP_CLASS = ".ballot_group";
var PREVIOUS_PARTY_AFFILIATIONS_SELECT_CLASS = "select.previous-party-affiliations";


var setup_ballot_select2 = function(ballots) {
  $(BALLOT_INPUT_CLASS).each(function(el) {
    var BallotInput = $(this);
    var ballot_group = BallotInput.closest(BALLOT_GROUP_CLASS);
    var party_list_input = ballot_group.find(PARTY_LIST_POSITION_INPUT_CLASS).parent();
    party_list_input.hide();
    var BallotSelect = $("<select>")
      .attr("id", BallotInput.attr("id"))
      .attr("name", BallotInput.attr("name"))
      .append($(ballots))
      .val(BallotInput.val())
      .insertAfter(BallotInput);
    BallotInput.hide().attr("required", false);

    BallotSelect.select2({
      placeholder: "Select a ballot",
      width: '100%',
      allowClear: true
    });
    BallotSelect.on('select2:select', function (e) {
      var selected_ballot = $(e.params.data.element);
      var uses_party_lists = selected_ballot.data("usesPartyLists");
      if (uses_party_lists === "True") {
        party_list_input.show();
      } else {
        party_list_input.hide();
      }

     var register =  selected_ballot.data("partyRegister");
     var current_register = $(ballot_group).data("partyRegister")
      if (register !== current_register) {
        $(ballot_group).find(PARTY_WIDGET_SELECT_CLASS).val(null).trigger('change');
        $(ballot_group).find(PARTY_WIDGET_INPUT_CLASS).val(null);
      }
     $(ballot_group).data("partyRegister", register);
    });
    var selected_data = BallotSelect.select2("data");
    if ($.isEmptyObject(selected_data) !== true) {
      BallotSelect.trigger({
        type: 'select2:select',
        params: {
          data: selected_data[0]
        }
      });
    }
  });
};

var populate_ballot_selects = function() {
  $(PARTY_LIST_POSITION_INPUT_CLASS).each(function() {
    var el= $(this);
    var selected_ballot = el.parents(BALLOT_GROUP_CLASS);

    var uses_party_lists = selected_ballot.data("usesPartyLists");
    if (uses_party_lists === "True") {
      el.parent().show();
    } else {
      if (el.val() === "") {
        el.parent().hide();
      }
    }
  });

  $.ajax({
    url: "/ajax/ballots/ballots_for_select.json",
    success: function(result){
      setup_ballot_select2(result);
    }
  });
};

var setup_single_party_select = function(i, partySelect) {
  var select_options = {
    width: '100%',
    placeholder: 'Select a party',
    allowClear: true
  };
  partySelect = $(partySelect);
  var ballot_group = partySelect.closest(BALLOT_GROUP_CLASS);
  var data = {
    id: 0,
    text: 'Click to load more parties…'
  };
  var loadMoreOption = new Option(data.text, data.id, false, false);
  partySelect.append(loadMoreOption);

  select_options.matcher = function(params, data) {
    var match = partySelect.select2.defaults.defaults.matcher(params, data);
    if (match) {
      var party_register;
      var selected_register = $(ballot_group).data("partyRegister");
      if (data.children !== undefined) {
        party_register =  data.children[0].element.getAttribute("register");
      } else {
        party_register = match.element.getAttribute("register");
      }
      if (selected_register === party_register) {
        return match;
      } else if (party_register === "all") {
        return match;
      } else if (party_register === null) {
        return match;
      } else {
        return null;
      }
    }
    if (data.id === "0") {
      return data;
    } else {
      return null;
    }
  };
  partySelect.on('select2:select', function (e) {
    var data = e.params.data;
    var party_input = $(ballot_group.find(PARTY_WIDGET_INPUT_CLASS));
    if (data.id === "0") {
      var initial_val = partySelect.val();
      data.text = "Loading…";
      partySelect.trigger('change.select2');

      $.getJSON('/all-parties.json', function(items) {
        $.each(items['items'], function(i, descs) {

          if (descs['children']) {
            var group = $('<optgroup label="' + descs.text + '" />');
            group.attr("data-register", descs.register);
            $.each(descs['children'], function(i, child) {
              var newOption = new Option(child.text, child.id, false, false);
              group.append(newOption);
            });
            group.appendTo(partySelect);
          } else {
            var newOption = new Option(descs.text, descs.id, false, false);
            $(newOption).attr("data-register", descs.register);
            $(newOption).appendTo(partySelect);
          }

        });
        partySelect.find('option[value="0"]').remove();
        partySelect.select2("open");
      });
    } else {
      party_input.val(e.params.data.id);
    }
    // when "cross" icon clicked to unselect a party clear the party input field
    partySelect.on('select2:clear', function(e) {
      party_input.val("")
    });
  });


  partySelect.select2(select_options);
};

var populate_party_selects = function() {
  var allPartySelects = $(PARTY_WIDGET_SELECT_CLASS);
  allPartySelects.attr("disabled", false);
  $(PARTY_WIDGET_INPUT_CLASS).hide();
  allPartySelects.each(setup_single_party_select);
};

var setup_multiple_party_select = function(i, partySelect) {
  var allPrevPartySelects = $(PREVIOUS_PARTY_AFFILIATIONS_SELECT_CLASS);
  allPrevPartySelects.attr("disabled", false);
  $(PREVIOUS_PARTY_AFFILIATIONS_SELECT_CLASS).hide();
  $(PREVIOUS_PARTY_AFFILIATIONS_SELECT_CLASS).select2({
    width: '100%',
    placeholder: 'Select previous party affiliations',
    allowClear: true,
    closeOnSelect: true,
    multiple: true,
  })
} 

var populate_prev_party_selects = function() {
  var allPrevPartySelects = $(PREVIOUS_PARTY_AFFILIATIONS_SELECT_CLASS);
  allPrevPartySelects.each(setup_multiple_party_select);
};


$(document).ready(function() { 
  populate_ballot_selects();
  populate_party_selects();
  populate_prev_party_selects();
  addTitleCaseButton(); 
});



/* This title-casing function should uppercase any letter after a word
   boundary, and lowercases any letters up to the next word boundary:
     toTitleCase("john travolta") => "John Travolta"
     toTitleCase("olivia newton-john") => "Olivia Newton-John"
     toTitleCase("miles o'brien") => "Miles O'Brien"
     toTitleCase("miles o’brien") => "Miles O’Brien"
     toTitleCase("BENJAMIN SISKO") => "Benjamin Sisko"
*/
function toTitleCase(str) {
  return str.replace(/\b(\w)(.*?)\b/g, function (_, first, rest) { return first.toUpperCase() + rest.toLowerCase() })
}

function compressWhitespace(str) {
  return str.replace(/\s\s+/g, ' ');
}

function addTitleCaseButton() {
  var name_fields = document.querySelectorAll('.person_name');
  for (let i = 0; i < name_fields.length; i++) {
    let btn = document.createElement("button");
    btn.innerHTML = "Title Case";
    btn.type = "button";
    btn.className = "titleCaseNameField button tiny secondary"
    name_fields[i].insertAdjacentElement('afterend', btn);
    btn.addEventListener('click', function() {
      let name = name_fields[i].value;
      name_fields[i].value = compressWhitespace(toTitleCase(name));
    })
  }
}

function addPreviousParty(){
  var prev_party_btns = document.querySelectorAll('.previous-party-btn');
  var prev_party_label = document.querySelectorAll('.previous-party-label');
  var input_fields = document.querySelectorAll('.previous-party-input');
  for (let i = 0; i < prev_party_btns.length; i++) {
    prev_party_btns[i].addEventListener('click', function() {
      prev_party_btns[i].style.display = 'none';
      prev_party_label[i].style.display = 'inline'; 
      input_fields[i].style.display = 'inline';
    })
  }
}