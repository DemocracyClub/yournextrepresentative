"use strict";
var BALLOT_INPUT_CLASS = "input.js-ballot-input";
var PARTY_WIDGET_SELECT_CLASS = "select.party_widget_select";
var PARTY_WIDGET_INPUT_CLASS = "input.party_widget_input";
var PARTY_LIST_POSITION_INPUT_CLASS = "input.party-list-position";


var setup_ballot_select2 = function(ballots) {
  $(BALLOT_INPUT_CLASS).each(function(el) {
    var BallotInput = $(this);
    var ballot_formset = BallotInput.closest("fieldset");
    var party_list_input = ballot_formset.find(PARTY_LIST_POSITION_INPUT_CLASS).parent();
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
     var current_register = $(ballot_formset).data("partyRegister")
      if (register !== current_register) {
        $(ballot_formset).find(PARTY_WIDGET_SELECT_CLASS).val(null).trigger('change');
        $(ballot_formset).find(PARTY_WIDGET_INPUT_CLASS).val(null);
      }
     $(ballot_formset).data("partyRegister", register)
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


  })
}

var populate_ballot_selects = function() {
  var BallotInput = $(BALLOT_INPUT_CLASS)

  $(PARTY_LIST_POSITION_INPUT_CLASS).each(function() {
    var el= $(this);
    if (el.val() === "") {
      el.parent().hide();
    }
  })

  BallotInput.select2();
  $.ajax({
    url: "/ajax/ballots/ballots_for_select.json",
    success: function(result){
      setup_ballot_select2(result)
    }
  })

}

var setup_single_party_select = function(i, partySelect) {
  var select_options = {
    width: '100%',
    placeholder: 'Select a party',
    allowClear: true,
  }
  partySelect = $(partySelect);
  var ballot_formset = partySelect.closest("fieldset");
  var data = {
    id: 0,
    text: 'Click to load more parties…'
  };
  var loadMoreOption = new Option(data.text, data.id, false, false);
  partySelect.append(loadMoreOption)

  select_options.matcher = function(params, data) {
    var match = partySelect.select2.defaults.defaults.matcher(params, data);
    if (match) {
      var party_register;
      var selected_register = $(ballot_formset).data("partyRegister");
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
      return null
    }
  }
  partySelect.on('select2:select', function (e) {
    var data = e.params.data;
    if (data.id === "0") {
      var initial_val = partySelect.val();
      data.text = "Loading…"
      partySelect.trigger('change.select2');

      $.getJSON('/all-parties.json', function(items) {
        $.each(items['items'], function(i, descs) {
          var group = $('<optgroup label="' + descs.text + '" />');
          group.attr("data-register", descs.register)
          if (descs['children']) {
            $.each(descs['children'], function(i, child) {
              // $('<option value="'+this.id+'"/>').html(this.text).appendTo(group);
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
        partySelect.select2('open');
      });
    } else {
      var party_input = $(ballot_formset.find(PARTY_WIDGET_INPUT_CLASS));
      party_input.val(e.params.data.id);
    }
  });
  partySelect.select2(select_options);
}

var populate_party_selects = function() {

  var allPartySelects = $(PARTY_WIDGET_SELECT_CLASS)
  allPartySelects.attr("disabled", false);
  $(PARTY_WIDGET_INPUT_CLASS).hide();
  allPartySelects.each(setup_single_party_select);

}
// // Ballot input widget
// $(BALLOT_INPUT_CLASS).each(function(el) {
//   var BallotInput = $(this);
//   var BallotSelect = $("<select>")
//     .val(BallotInput.val())
//     .attr("id", BallotInput.attr("id"))
//     .attr("name", BallotInput.attr("name"))
//     .insertAfter(BallotInput);
//   BallotInput.hide();
//
//
//   var select_options = {
//     width: '100%',
//     allowClear: true,
//     multiple: false,
//     maximumSelectionSize: 1,
//     placeholder: "Start typing",
//     // data: getBallotData(),
//     // ajax: {
//     //   url: '/ajax/ballots/ballots_for_select.json',
//     //   dataType: 'json',
//     //   // processResults: function (data) {
//     //   //   return {
//     //   //     results: $.map(data.results, function (obj) {
//     //   //       return {
//     //   //         id: obj.id,
//     //   //         text: obj.text,
//     //   //         party_register: obj.party_register_id
//     //   //       };
//     //   //     })
//     //   //   };
//     //   // },
//     //   cache: true,
//
//
//     // },
//     templateSelection: function (data, container) {
//       // Add custom attributes to the <option> tag for the selected option
//       console.debug(data);
//       $(data.element).attr('data-party_register', data.party_register_id);
//       return data.text;
//     }
//   }
//   BallotSelect.select2(select_options);
//   BallotSelect.on("select2:select", function(selected) {
//     console.debug(BallotSelect.find(':selected').data('party_register'));
//   })
// })



// }


$(document).ready(function() {
  populate_ballot_selects()
  populate_party_selects()
});



// /* This is a variant of the suggestion in the jQuery FAQ:
//      https://learn.jquery.com/using-jquery-core/faq/how-do-i-select-an-element-by-an-id-that-has-characters-used-in-css-notation/
//    We need this since election IDs now have dots in them.
//  */
// function escapeID(originalID) {
//   return originalID.replace( /(:|\.|\[|\]|,)/g, "\\$1" );
// }
//
//
// /* Change the visibility of a Select2 widget; select2Element should be a
//    jQuery-wrapped element */
//
// function setSelect2Visibility(select2Element, visibility) {
//   /* If visibility is false, this both disables the Select2 boxes and
//    * hides them by hiding their enclosing element. Otherwise it
//    * enables it and makes the enclosure visible. */
//   select2Element.prop(
//     'disabled',
//     !visibility
//   );
//
//   if (visibility) {
//     select2Element.parent().show()
//   } else {
//     select2Element.parent().hide();
//   }
// }
//
// /* Make all the party drop-downs into Select2 widgets */
//
// function setUpPartySelect2s() {
//   var party_selects = $("select.party-select");
//   party_selects.not('.select2-offscreen').not('.select2-container').each(function(i) {
//     var partySelect = $(this)
//     var select_options = {
//       width: '100%',
//       placeholder: 'Select a party',
//       allowClear: true
//     }
//
//     if (partySelect.attr('show_load_more')) {
//       var data = {
//           id: 0,
//           text: 'Click to load more parties…'
//       };
//       var loadMoreOption = new Option(data.text, data.id, false, false);
//       partySelect.append(loadMoreOption)
//
//       select_options.matcher = function(params, data) {
//         var match = partySelect.select2.defaults.defaults.matcher(params, data);
//         if (match) {
//           return match;
//         }
//         if (data.id === "0") {
//           return data;
//         } else {
//           return null
//         }
//       }
//       partySelect.on('select2:select', function (e) {
//           var data = e.params.data;
//           if (data.id == 0) {
//             var initial_val = partySelect.val();
//             var partyset = $(this).data('partyset').toUpperCase();
//             // partySelect.find('option[value="0"]').text('Loading…');
//             data.text = "Loading…"
//             partySelect.trigger('change.select2');
//
//             $.getJSON('/all-parties.json?register=' + partyset, function(items) {
//               $.each(items['items'], function(party_id, descs) {
//                 var group = $('<optgroup label="' + descs.text + '" />');
//                 if (descs['children']) {
//                   $.each(descs['children'], function(child) {
//                     $('<option value="'+this.id+'"/>').html(this.text).appendTo(group);
//                   });
//                 } else {
//                     $('<option value="'+descs.id+'"/>').html(descs.text).appendTo(group);
//                 }
//                 group.appendTo(partySelect);
//               });
//               partySelect.find('option[value="0"]').remove();
//               partySelect.select2('open');
//             });
//
//
//
//
//
//           }
//       });
//
//     }
//
//     partySelect.select2(select_options);
//   });
//
//   var post_select_exists = $(".post-select").length;
//   if (post_select_exists && party_selects.length > 1) {
//     /* If there is more than one party list, only show GB parties by default */
//     party_selects.each(function(i, el) {
//       if (el.name.indexOf("party_GB") !== 0){
//           var select_el = $(escapeID("#" + el.dataset["select2Id"]));
//           setSelect2Visibility(select_el, false);
//       }
//     });
//   }
//
// }
//
// $(document).on('focus', '.select2.select2-container', function (e) {
//   // only open on original attempt - close focus event should not fire open
//   if (e.originalEvent && $(this).find(".select2-selection--single").length > 0) {
//     $(this).siblings('select').select2('open');
//   }
// });
//
//
// /* Make all the post drop-downs into Select2 widgets */
//
// function setUpPostSelect2s() {
//   $('.post-select').each(function(i) {
//     var postSelect = $(this),
//       hidden = postSelect.prop('tagName') == 'INPUT' &&
//          postSelect.attr('type') == 'hidden';
//     /* If it's a real select box (not a hidden input) make it into a
//      * Select2 box; also, don't try to reinitialize a select that's
//      * already a Select2 */
//     if (!(hidden || $(postSelect).data('select2'))) {
//         var select_config = {
//         placeholder: 'Post',
//         allowClear: true,
//         width: '100%'
//       }
//       if (postSelect.prop('show_load_more')) {
//           var load_more_option = {
//               id: 0,
//               text: 'Load more parties…'
//           }
//           postSelect.append(load_more_option)
//           // select_config.
//       }
//       postSelect.select2(select_config);
//     }
//     postSelect.on('change', function (e) {
//       updateFields();
//     });
//     updateFields();
//   });
// }
//
// /* Set the visibility of an input element and any label for it */
//
// function setVisibility(plainInputElement, newVisiblity) {
//   var inputElement = $(plainInputElement),
//       inputElementID = escapeID(plainInputElement.id),
//       labelElement = $('label[for=' + inputElementID + ']');
//   inputElement.toggle(newVisiblity);
//   labelElement.toggle(newVisiblity);
// }
//
//
// /* Update the visibility of the party and post drop-downs for a particular
//    election */
//
// function updateSelectsForElection(show, election) {
//   /* Whether we should show the party and post selects is
//      determined by the boolean 'show'. */
//   var partySelectToShowID,
//       partyPositionToShowID,
//       postID = $('#id_constituency_' + escapeID(election)).val(),
//       partySet;
//   if (postID) {
//     partySet = postIDToPartySet[postID].toUpperCase();
//   }
//   if (show) {
//     if (postID) {
//       partySelectToShowID = 'id_party_' + partySet + '_' + election;
//       partyPositionToShowID = 'id_party_list_position_' + partySet + '_' + election;
//       $('.party-select-' + escapeID(election)).each(function(i) {
//         setSelect2Visibility(
//           $(this),
//           $(this).attr('id') == partySelectToShowID
//         );
//       });
//       $('.party-position-' + escapeID(election)).each(function(i) {
//         setVisibility(this, $(this).attr('id') == partyPositionToShowID);
//       });
//     }
//   } else {
//     $('.party-select-' + escapeID(election)).each(function(i) {
//       setSelect2Visibility($(this), false);
//     });
//     $('.party-position-' + escapeID(election)).each(function() {
//       setVisibility(this, false);
//     });
//   }
//   setSelect2Visibility($('#id_constituency_' + escapeID(election)), show);
// }
//
// /* Make sure that the party and constituency select boxes are updated
//    when you choose whether the candidate is standing in that election
//    or not. */
//
// function setUpStandingCheckbox() {
//   $('#person-details select.standing-select').on('change', function() {
//     updateFields();
//   });
// }
//
// /* This should be called whenever the select drop-downs for party
//    and post that have to be shown might have to be shown.  */
//
// function updateFields() {
//   $('#person-details select.standing-select').each(function(i) {
//     var standing = $(this).val() == 'standing',
//         match = /^id_standing_(.*)/.exec($(this).attr('id')),
//         election = match[1];
//     updateSelectsForElection(standing, election); });
// }
//
// /* This is called to display a new election form on the edit person
//    page, if the dynamic "add new election" button is being used. */
//
// function showElectionsForm() {
//   $.getJSON("/api/current-elections/?future=1").done(function( data ) {
//     var select_data = $.map(data, function(obj, key) {
//       return { id: key, text: obj.name + ' (' + obj.election_date + ')' };
//     })
//     $('#add_more_elections').select2({
//       data: select_data,
//     }).on('select2:select', function(e) {
//       var data = e.params.data;
//       var url = window.location.pathname + '/single_election_form/' + data.id;
//       $.get(url, function(data) {
//         $('.extra_elections_forms').html(data);
//         setUpStandingCheckbox();
//         setUpPartySelect2s();
//         setUpPostSelect2s();
//         updateFields();
//       });
//     });
//     $('.add_more_elections_field').show();
//     $('#add_election_button').hide();
//   });
// }
//
// /* This title-casing function should uppercase any letter after a word
//    boundary, and lowercases any letters up to the next word boundary:
//
//      toTitleCase("john travolta") => "John Travolta"
//      toTitleCase("olivia newton-john") => "Olivia Newton-John"
//      toTitleCase("miles o'brien") => "Miles O'Brien"
//      toTitleCase("miles o’brien") => "Miles O’Brien"
//      toTitleCase("BENJAMIN SISKO") => "Benjamin Sisko"
// */
// function toTitleCase(str) {
//     return str.replace(/\b(\w)(.*?)\b/g, function (_, first, rest) { return first.toUpperCase() + rest.toLowerCase() })
// }
//
// function compressWhitespace(str) {
//     return str.replace(/\s\s+/g, ' ');
// }
//
// suggest_correction = function(el, suggestion) {
//
//     suggestion_el = $('<a class="suggested">Change to <span>' + suggestion + '</span>?</a>');
//     suggestion_el.click(function(clicked_el) {
//         var this_link = $(this);
//         this_link.prev('input').val($(this_link).find('span').text());
//         $('.suggested').remove();
//     })
//     $('.suggested').remove();
//     $(el).after(suggestion_el);
//
// };
//
// function checkNameFormat(e) {
//     var name = e.target.value;
//     var upper_first_matcher = /([A-Z]+,? [A-Za-z]+)/g;
//     var match = upper_first_matcher.exec(name);
//     if (match) {
//         var name_parts = name.split(' ');
//         var last_name = name_parts.shift();
//         var name = name_parts.join(' ') + ' ' + toTitleCase(last_name);
//         suggest_correction(e.target, name);
//     }
// }
//
// function addTitleCaseButton() {
//     var buttons = $('.titleCaseNameField');
//     buttons.each(function() {
//         button_el = $(this);
//         $(this).on('click', function() {
//             this_name_field = button_el.parent().find('#id_name');
//             name_val = this_name_field.val();
//             this_name_field.val(compressWhitespace(toTitleCase(name_val)));
//             return false;
//         })
//     });
// }
//
// $(document).ready(function() {
//   $.getJSON('/post-id-to-party-set.json', function(data) {
//       window.postIDToPartySet = data;
//       setUpPartySelect2s();
//       setUpPostSelect2s();
//       setUpStandingCheckbox();
//       updateFields();
//       /* Now enable the "add an extra election" button if it's present */
//       $('#add_election_button').on('click', showElectionsForm);
//       $('.add_more_elections_field').hide();
//       /* Check for the common name form like "SMITH Ali" found on
//          SOPNs and suggest changing it to "Ali Smith" in any name
//          fields */
//       $('[name=name]').on('paste keyup', checkNameFormat);
//       $('[name*=-name]').on('paste keyup', checkNameFormat);
//   });
//   // general page set up functions
//   addTitleCaseButton()
//
// });
