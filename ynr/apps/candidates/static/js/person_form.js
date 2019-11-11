/* This is a variant of the suggestion in the jQuery FAQ:
     https://learn.jquery.com/using-jquery-core/faq/how-do-i-select-an-element-by-an-id-that-has-characters-used-in-css-notation/
   We need this since election IDs now have dots in them.
 */
function escapeID(originalID) {
  return originalID.replace( /(:|\.|\[|\]|,)/g, "\\$1" );
}


/* Change the visibility of a Select2 widget; select2Element should be a
   jQuery-wrapped element */

function setSelect2Visibility(select2Element, visibility) {
  /* If visibility is false, this both disables the Select2 boxes and
   * hides them by hiding their enclosing element. Otherwise it
   * enables it and makes the enclosure visible. */
  select2Element.prop(
    'disabled',
    !visibility
  );

  if (visibility) {
    select2Element.parent().show()
  } else {
    select2Element.parent().hide();
  }
}

/* Make all the party drop-downs into Select2 widgets */

function setUpPartySelect2s() {
  var party_selects = $("select.party-select");
  party_selects.not('.select2-offscreen').not('.select2-container').each(function(i) {
    var partySelect = $(this)
    var select_options = {
      width: '100%',
      placeholder: 'Select a party',
      allowClear: true
    }

    if (partySelect.attr('show_load_more')) {
      var data = {
          id: 0,
          text: 'Click to load more parties…'
      };
      var loadMoreOption = new Option(data.text, data.id, false, false);
      partySelect.append(loadMoreOption)

      select_options.matcher = function(params, data) {
        var match = partySelect.select2.defaults.defaults.matcher(params, data);
        if (match) {
          return match;
        }
        if (data.id === "0") {
          return data;
        } else {
          return null
        }
      }
      partySelect.on('select2:select', function (e) {
          var data = e.params.data;
          if (data.id == 0) {
            var initial_val = partySelect.val();
            var partyset = $(this).data('partyset').toUpperCase();
            // partySelect.find('option[value="0"]').text('Loading…');
            data.text = "Loading…"
            partySelect.trigger('change.select2');

            $.getJSON('/all-parties.json?register=' + partyset, function(items) {
              $.each(items['items'], function(party_id, descs) {
                var group = $('<optgroup label="' + descs.text + '" />');
                if (descs['children']) {
                  $.each(descs['children'], function(child) {
                    $('<option value="'+this.id+'"/>').html(this.text).appendTo(group);
                  });
                } else {
                    $('<option value="'+descs.id+'"/>').html(descs.text).appendTo(group);
                }
                group.appendTo(partySelect);
              });
              partySelect.find('option[value="0"]').remove();
              partySelect.select2('open');
            });





          }
      });

    }

    partySelect.select2(select_options);
  });

  var post_select_exists = $(".post-select").length;
  if (post_select_exists && party_selects.length > 1) {
    /* If there is more than one party list, only show GB parties by default */
    party_selects.each(function(i, el) {
      if (el.name.indexOf("party_GB") !== 0){
          var select_el = $(escapeID("#" + el.dataset["select2Id"]));
          setSelect2Visibility(select_el, false);
      }
    });
  }

}

$(document).on('focus', '.select2', function (e) {
  if (e.originalEvent) {
    $(this).siblings('select').select2('open');
  }
});


/* Make all the post drop-downs into Select2 widgets */

function setUpPostSelect2s() {
  $('.post-select').each(function(i) {
    var postSelect = $(this),
      hidden = postSelect.prop('tagName') == 'INPUT' &&
         postSelect.attr('type') == 'hidden';
    /* If it's a real select box (not a hidden input) make it into a
     * Select2 box; also, don't try to reinitialize a select that's
     * already a Select2 */
    if (!(hidden || $(postSelect).data('select2'))) {
        var select_config = {
        placeholder: 'Post',
        allowClear: true,
        width: '100%'
      }
      if (postSelect.prop('show_load_more')) {
          var load_more_option = {
              id: 0,
              text: 'Load more parties…'
          }
          postSelect.append(load_more_option)
          // select_config.
      }
      postSelect.select2(select_config);
    }
    postSelect.on('change', function (e) {
      updateFields();
    });
    updateFields();
  });
}

/* Set the visibility of an input element and any label for it */

function setVisibility(plainInputElement, newVisiblity) {
  var inputElement = $(plainInputElement),
      inputElementID = escapeID(plainInputElement.id),
      labelElement = $('label[for=' + inputElementID + ']');
  inputElement.toggle(newVisiblity);
  labelElement.toggle(newVisiblity);
}


/* Update the visibility of the party and post drop-downs for a particular
   election */

function updateSelectsForElection(show, election) {
  /* Whether we should show the party and post selects is
     determined by the boolean 'show'. */
  var partySelectToShowID,
      partyPositionToShowID,
      postID = $('#id_constituency_' + escapeID(election)).val(),
      partySet;
  if (postID) {
    partySet = postIDToPartySet[postID].toUpperCase();
  }
  if (show) {
    if (postID) {
      partySelectToShowID = 'id_party_' + partySet + '_' + election;
      partyPositionToShowID = 'id_party_list_position_' + partySet + '_' + election;
      $('.party-select-' + escapeID(election)).each(function(i) {
        setSelect2Visibility(
          $(this),
          $(this).attr('id') == partySelectToShowID
        );
      });
      $('.party-position-' + escapeID(election)).each(function(i) {
        setVisibility(this, $(this).attr('id') == partyPositionToShowID);
      });
    }
  } else {
    $('.party-select-' + escapeID(election)).each(function(i) {
      setSelect2Visibility($(this), false);
    });
    $('.party-position-' + escapeID(election)).each(function() {
      setVisibility(this, false);
    });
  }
  setSelect2Visibility($('#id_constituency_' + escapeID(election)), show);
}

/* Make sure that the party and constituency select boxes are updated
   when you choose whether the candidate is standing in that election
   or not. */

function setUpStandingCheckbox() {
  $('#person-details select.standing-select').on('change', function() {
    updateFields();
  });
}

/* This should be called whenever the select drop-downs for party
   and post that have to be shown might have to be shown.  */

function updateFields() {
  $('#person-details select.standing-select').each(function(i) {
    var standing = $(this).val() == 'standing',
        match = /^id_standing_(.*)/.exec($(this).attr('id')),
        election = match[1];
    updateSelectsForElection(standing, election); });
}

/* This is called to display a new election form on the edit person
   page, if the dynamic "add new election" button is being used. */

function showElectionsForm() {
  $.getJSON("/api/current-elections/?future=1").done(function( data ) {
    var select_data = $.map(data, function(obj, key) {
      return { id: key, text: obj.name + ' (' + obj.election_date + ')' };
    })
    $('#add_more_elections').select2({
      data: select_data,
    }).on('select2:select', function(e) {
      var data = e.params.data;
      var url = window.location.pathname + '/single_election_form/' + data.id;
      $.get(url, function(data) {
        $('.extra_elections_forms').html(data);
        setUpStandingCheckbox();
        setUpPartySelect2s();
        setUpPostSelect2s();
        updateFields();
      });
    });
    $('.add_more_elections_field').show();
    $('#add_election_button').hide();
  });
}

function toTitleCase(str) {
    return str.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
}

function compressWhitespace(str) {
    return str.replace(/\s\s+/g, ' ');
}

suggest_correction = function(el, suggestion) {

    suggestion_el = $('<a class="suggested">Change to <span>' + suggestion + '</span>?</a>');
    suggestion_el.click(function(clicked_el) {
        var this_link = $(this);
        this_link.prev('input').val($(this_link).find('span').text());
        $('.suggested').remove();
    })
    $('.suggested').remove();
    $(el).after(suggestion_el);

};

function checkNameFormat(e) {
    var name = e.target.value;
    var upper_first_matcher = /([A-Z]+,? [A-Za-z]+)/g;
    var match = upper_first_matcher.exec(name);
    if (match) {
        var name_parts = name.split(' ');
        var last_name = name_parts.shift();
        var name = name_parts.join(' ') + ' ' + toTitleCase(last_name);
        suggest_correction(e.target, name);
    }
}

function addTitleCaseButton() {
    var b = $('<button type="button" class="button tiny secondary">Title Case</botton>');
    b.on('click', function() {
        var name_val = $('#id_name').val();
        $('#id_name').val(compressWhitespace(toTitleCase(name_val)));
        return false;
    });
    $('#id_name').after(b);
}

$(document).ready(function() {
  $.getJSON('/post-id-to-party-set.json', function(data) {
      window.postIDToPartySet = data;
      setUpPartySelect2s();
      setUpPostSelect2s();
      setUpStandingCheckbox();
      updateFields();
      /* Now enable the "add an extra election" button if it's present */
      $('#add_election_button').on('click', showElectionsForm);
      $('.add_more_elections_field').hide();
      /* Check for the common name form like "SMITH Ali" found on
         SOPNs and suggest changing it to "Ali Smith" in any name
         fields */
      $('[name=name]').on('paste keyup', checkNameFormat);
      $('[name*=-name]').on('paste keyup', checkNameFormat);
  });
});
