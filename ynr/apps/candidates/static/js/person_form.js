"use strict";
var BALLOT_INPUT_CLASS = "input.js-ballot-input:not(:hidden)";
var PARTY_WIDGET_SELECT_CLASS = "select.party_widget_select";
var PARTY_WIDGET_INPUT_CLASS = "input.party_widget_input";
var PARTY_LIST_POSITION_INPUT_CLASS = "input.party-list-position";
var BALLOT_GROUP_CLASS = ".ballot_group";

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
    BallotInput.hide();

    BallotSelect.select2();
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
  var BallotInput = $(BALLOT_INPUT_CLASS);

  $(PARTY_LIST_POSITION_INPUT_CLASS).each(function() {
    var el= $(this);
    if (el.val() === "") {
      el.parent().hide();
    }
  });

  BallotInput.select2();
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
    if (data.id === "0") {
      var initial_val = partySelect.val();
      data.text = "Loading…";
      partySelect.trigger('change.select2');

      $.getJSON('/all-parties.json', function(items) {
        $.each(items['items'], function(i, descs) {
          var group = $('<optgroup label="' + descs.text + '" />');
          group.attr("data-register", descs.register);
          if (descs['children']) {
            $.each(descs['children'], function(i, child) {
              var newOption = new Option(child.text, child.id, false, false);
              group.append(newOption);
            });
          } else {
            var newOption = new Option(descs.text.label, descs.id, false, false);
            group.append(newOption);
          }
          group.appendTo(partySelect);
        });
        partySelect.find('option[value="0"]').remove();
        partySelect.select2("open");
      });
    } else {
      var party_input = $(ballot_group.find(PARTY_WIDGET_INPUT_CLASS));
      party_input.val(e.params.data.id);
    }
  });
  partySelect.select2(select_options);
};

var populate_party_selects = function() {
  var allPartySelects = $(PARTY_WIDGET_SELECT_CLASS);
  allPartySelects.attr("disabled", false);
  $(PARTY_WIDGET_INPUT_CLASS).hide();
  allPartySelects.each(setup_single_party_select);
};

$(document).ready(function() {
  populate_ballot_selects();
  populate_party_selects()
});
