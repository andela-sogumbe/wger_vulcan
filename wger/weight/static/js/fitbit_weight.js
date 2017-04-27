// Set event listener on button
function prepFitbitWeightApiCall(){
  $getFitbitWeightBtn = $("#fitbit-weight-btn");
  if ($getFitbitWeightBtn.length){
    $getFitbitWeightBtn.click(function(){
        callFitbitWeightApi()
    });
  }
}

function callFitbitWeightApi(){
  $getFitbitWeightBtn.addClass("hidden");
  $fitbitAjaxLoader = $("#fitbit-ajax-loader");
  $fitbitAjaxLoader.html('<div style="text-align:center;">'+
        '<img src="/static/images/loader.svg" width="48" height="48">' +
    '</div>');


  userFitbitTokens = $("#fitbit-access-tokens").text().split(" ")
  weightDate = $("#id_date").val()

  // Request for weight from fitbit
  $.ajax({
  type: "GET",
  url: "https://api.fitbit.com/1/user/" +
    userFitbitTokens[2]+
      "/body/log/weight/date/" + weightDate + ".json",
  beforeSend: function (jqXHR) {
    access_token = userFitbitTokens[0]
    refresh_token = userFitbitTokens[1]
    jqXHR.setRequestHeader('Authorization', 'Bearer ' + access_token);
  },
  success: function (data, textStatus, jqXHR) {
     $weightField = $("#id_weight")
     // Set weight value from fitbit
     $weightField.val(data.weight[0].weight)
     $fitbitAjaxLoader.html("");
     $getFitbitWeightBtn.removeClass("hidden");
  },
  error: function (data, textStatus, jqXHR) {
    $fitbitAjaxLoader.html("");
    $fitbitAjaxLoader.text("Could not get your data");
    $getFitbitWeightBtn.removeClass("hidden");
  }
});
}

prepFitbitWeightApiCall()
