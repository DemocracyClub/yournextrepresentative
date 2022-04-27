$(function() {
  var toggleFullVersion = function toggleFullVersion($fullVersion){
    if($fullVersion.is(':visible')){
      $fullVersion.hide().siblings('.js-toggle-full-version-json').text('Show full version');
    } else {
      $fullVersion.show().siblings('.js-toggle-full-version-json').text('Hide full version');
    }
  }

  toggleFullVersion($('.full-version-json'));

  $('.js-toggle-full-version-json').on('click', function(){
    toggleFullVersion($(this).siblings('.full-version-json'));
  });

  hideAllDiffRows();
  toggleDiffRow();  
});

function hideAllDiffRows() {
  var $recentChanges = $('table.recent-changes');
  $recentChanges.find('tbody.diff-row').hide();
}

function toggleDiffRow() { 
	var $recentChanges = $('table.recent-changes');
  $recentChanges.find('button.js-toggle-diff-row').on('click', function(){
    $(this).closest('tbody').next('tbody').toggle();
    if($(this).text() == 'Show'){
      $(this).text('Hide');
    } else {
      $(this).text('Show');
    }
  });
}

