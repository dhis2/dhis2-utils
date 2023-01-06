
var arrLang = {{ form_dict }}

console.log("Applying translations");
$(function() {
  $.ajax({
    type: "GET",
    url: "../api/me.json",
    success: function(data) {
      if ("settings" in data) {
        var locale = data.settings.keyDbLocale;
        console.log("DB Locale: " + locale);
      } else {
        var locale = document.documentElement.lang;
        console.log("Could not get DB locale, using UI locale: " + locale);
      }
      changeLanguage(locale);
    },
    error: function() {}
  });

  function changeLanguage(lang) {
    $(".lang").each(function(index, element) {
      if(lang in arrLang) {
        if($(this).attr("langkey") in arrLang[lang]) {
          $(this).html(arrLang[lang][$(this).attr("langkey")]);
        }
      }
    });
  }
});
