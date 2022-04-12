$(function(){
    $('body').removeClass('no-js').addClass('js');

    $('.js-bulk-known-person-not-standing').on('click', function(e){
        e.preventDefault();

        $person = $(this).parents('tr');
        $people_table = $person.parents('table');
        $link = $person.find('.js-bulk-known-person-not-standing');
        var $form = $people_table.find('form').parents("tr");
        // don't add the form twice
        $form.remove().end();
        $form = $( $('.js-bulk-known-person-not-standing-form').html() );
        $form.insertAfter($person);

        $form.find('input[type="text"]').focus();

        $form.on('submit', function(){
            $form.find('#candidacyerr').remove();
            $form.find('.alert').remove();
            $form.find('.errorlist').remove();
            $source = $form.find('input[name="source"]').val();
            $.ajax({
                url: $link.attr('href'),
                type: "POST",
                data: {
                    csrfmiddlewaretoken: $form.find('input[type="hidden"]').val(),
                    person_id: $link.data('person-id'),
                    post_id: $link.data('post-id'),
                    source : $form.find('input[name="source"]').val()
                },

                success: function(json) {
                    if (json['success']) {
                        $person.remove();
                    } else {
                        if (json['errors']) {
                            for (var err in json.errors) {
                                if (!json.errors.hasOwnProperty(err)) { continue; }
                                el = $form.find('input[name="' + err + '"]');
                                el.before('<ul class="errorlist"><li>' + json.errors[err] + '</li></ul>')
                            }
                        }
                    }
                },

                error: function(xhr,errmsg,err) {
                    $form.prepend("<div class='alert-box alert radius' id='candidacyerr'>There was a problem removing the candidacy, please try again</div>");
                }
            });
            return false;
        });


        $form.on('click', '.js-bulk-known-person-not-standing-cancel', function(){
            $form.remove();
        });
    });

    $('.js-bulk-known-person-alternate-name').on('click', function(e){
        e.preventDefault();

        $person = $(this).parents('tr');
        $people_table = $person.parents('table');
        $link = $person.find('.js-bulk-known-person-alternate-name');
        var $form = $people_table.find('form').parents("tr");
        $form.remove().end();

        $form = $( $('.js-bulk-known-person-alternate-name-form').html() );
        $form.insertAfter($person);

        $form.find('input[type="text"]').focus();

        $form.on('submit', function(){
            $form.find('#altnameerr').remove();
            $form.find('.alert').remove();
            $form.find('.errorlist').remove();
            $name = $form.find('input[name="name"]').val();
            $.ajax({
                url: $link.attr('href'),
                type: "POST",
                data: {
                    csrfmiddlewaretoken: $form.find('input[type="hidden"]').val(),
                    name : $name,
                    source : $form.find('input[name="source"]').val()
                },

                success: function(json) {
                    if (json['success']) {
                        $other = $person.find('.other-names');
                        if ($other.length == 0) {
                            $first_name = $person.find('>:first-child');
                            $first_name.after('<ul class="other-names clearfix"><li>Other names:</li></ul>');
                            $other = $person.find('.other-names');
                        }
                        $names = $other.find('.other-name');
                        $names.remove()
                        for (var i = 0; i < json.names.length; i++) {
                            var name = json.names[i];
                            var highlight = '';
                            if (name == $name) {
                                highlight = ' highlight';
                            }
                            $other.append('<li class="other-name' + highlight + '">' + json.names[i] + '</li>');
                        }
                        $form.remove();
                    } else {
                        if (json['errors']) {
                            for (var err in json.errors) {
                                if (!json.errors.hasOwnProperty(err)) { continue; }
                                el = $form.find('input[name="' + err + '"]');
                                el.before('<ul class="errorlist"><li>' + json.errors[err] + '</li></ul>')
                            }
                        }
                    }
                },

                error: function(xhr,errmsg,err) {
                    $form.prepend("<div class='alert-box alert radius' id='altnameerr'>There was a problem adding the name, please try again</div>");
                }
            });
            return false;
        });

        $form.on('click', '.js-bulk-known-person-alternate-name-cancel', function(){
            $form.remove();
        });
    });


    function tbody_is_empty($tbody) {
      if ($tbody.find("input:not([type=hidden])").val() && $tbody.find("input:not([type=hidden])").val().length > 0) {
        return false;
      }
      if ($tbody.find("option:not([value='']):selected").length > 0) {
        return false;
      }
      return true;
    }

    // Remove empty fieldsets
    var always_show_extra = $("form#bulk_add_form")[0].dataset.winnerCount * 3;
    $("#bulk_add_form .sopn_adding_table tbody").each(function(i) {
      var tbody = $(this);
      if (tbody_is_empty(tbody)) {
        if (i >= always_show_extra) {
          tbody.hide();
          tbody.prev("thead").hide();
        }
      } else {
        always_show_extra++;
      }
    });


    // Extra form rows on bulk adding form
    var $table = $("#bulk_add_form .sopn_adding_table");
    var add_extra_row = "<tbody class='add_extra_table'><tr><td></td><td><button type='button' id='add_row_button'>Add row</button></td></tr></tbody>";
    $table.append(add_extra_row);
    $("#add_row_button").on("click", function() {
      var total_form_element = $('#id_form-TOTAL_FORMS');
      var last_tbody = $table.find("tbody:last").prev("tbody");
      var new_tbody = last_tbody.clone(true, true);
      var formRegex = RegExp('form-[1-9]+-','g');
      var new_form_id = $table.find(".ballot_group").length;
      new_tbody.html(new_tbody.html().replace(formRegex, 'form-'+new_form_id+'-'));
      var next_form_id = new_form_id += 1;
      var next_form_label = $table.find("thead:visible:last").find("th").text().match("([0-9]+)")[0];
      next_form_label = parseInt(next_form_label) + 1;
      $("<thead><tr><th colspan='3' >Person "+ next_form_label +"</th></tr></thead>").insertBefore($(".add_extra_table"));
      new_tbody.insertBefore($(".add_extra_table"));
      new_tbody.find(".select2").remove();
      populate_party_selects();
      new_tbody.show();
      total_form_element.val(next_form_id);
    });

});
