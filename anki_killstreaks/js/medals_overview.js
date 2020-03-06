(function($) {
  $('#game_select').change(function() {
    var value = this.selectedOptions[0].value;

    $('.game-medals').each(function() {
      var isSelectedGame = $(this).data("game-id") === value;
      var shouldShowAll = value === "_all";

      var shouldShowGame = isSelectedGame || shouldShowAll;

      this.classList.toggle("game-medals--current", shouldShowGame);
    });
    var ksElement = document.querySelector("#anki_killstreaks");
    var topOfKsElement = ksElement.getBoundingClientRect().top;

    window.scrollTo(window.scrollX, topOfKsElement);
  });
})(jQuery);
